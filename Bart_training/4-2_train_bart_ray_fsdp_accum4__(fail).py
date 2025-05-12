import ray
from ray.train.torch import TorchTrainer
from ray.train import ScalingConfig, RunConfig, CheckpointConfig
from ray.train.torch import FSDPConfig

from transformers import (
    BartTokenizer, BartForConditionalGeneration,
    TrainingArguments, Trainer
)
from datasets import load_dataset
import evaluate
import wandb
import numpy as np


def train_func():
    # Load the dataset from JSON files
    dataset = load_dataset("json", data_files={
        "train": "/workspace/QMSum-main/data/ALL/jsonl/train.jsonl",
        "validation": "/workspace/QMSum-main/data/ALL/jsonl/val.jsonl"
    })

    # Load the tokenizer and pre-trained model
    model_path = "/workspace/models/facebook/bart-large"
    tokenizer = BartTokenizer.from_pretrained(model_path)
    model = BartForConditionalGeneration.from_pretrained(model_path)

    # Define the preprocessing function for inputs and targets
    def preprocess_function(examples):
        inputs = ["question: " + q + " context: " + c for q, c in zip(examples["query"], examples["meeting_transcripts"])]
        model_inputs = tokenizer(inputs, max_length=1024, truncation=True, padding="max_length")

        with tokenizer.as_target_tokenizer():
            labels = tokenizer(examples["answer"], max_length=256, truncation=True, padding="max_length")
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    # Apply preprocessing to the dataset
    tokenized_datasets = dataset.map(preprocess_function, batched=True)

    # Load evaluation metrics
    rouge = evaluate.load("rouge")
    bleu = evaluate.load("bleu")
    meteor = evaluate.load("meteor")
    bertscore = evaluate.load("bertscore")

    # Define the evaluation metric computation function
    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        if isinstance(preds, np.ndarray) and preds.ndim == 3:
            preds = np.argmax(preds, axis=-1)

        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        decoded_preds = [pred.strip() for pred in decoded_preds]
        decoded_labels = [label.strip() for label in decoded_labels]

        result_rouge = rouge.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)
        result_bleu = bleu.compute(predictions=decoded_preds, references=[[ref] for ref in decoded_labels])
        result_meteor = meteor.compute(predictions=decoded_preds, references=decoded_labels)
        result_bertscore = bertscore.compute(predictions=decoded_preds, references=decoded_labels, lang="en")
        avg_bertscore_f1 = np.mean(result_bertscore["f1"])

        result = {
            "rouge1": round(result_rouge["rouge1"], 4),
            "rouge2": round(result_rouge["rouge2"], 4),
            "rougeL": round(result_rouge["rougeL"], 4),
            "bleu": round(result_bleu["bleu"], 4),
            "meteor": round(result_meteor["meteor"], 4),
            "bertscore_f1": round(avg_bertscore_f1, 4)
        }
        return result

    # Define training arguments for FSDP + gradient accumulation
    training_args = TrainingArguments(
        output_dir="/workspace/results_ray",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=5e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=4,  # accum=4 for comparison
        num_train_epochs=5,
        weight_decay=0.01,
        save_total_limit=2,
        logging_dir="/workspace/logs_ray",
        logging_steps=10,
        fp16=True,
        report_to="wandb",
        run_name="4-2) Ray_FSDP_accum4",  # Must match RunConfig.name
        eval_accumulation_steps=2,
    )

    # Initialize Hugging Face Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    # Start training
    trainer.train()


if __name__ == "__main__":
    # Initialize Ray and launch TorchTrainer with FSDP strategy
    ray.init()

    trainer = TorchTrainer(
        train_loop_per_worker=train_func,
        scaling_config=ScalingConfig(num_workers=2, use_gpu=True),
        run_config=RunConfig(
            name="4-2) Ray_FSDP_accum4",  # Must match run_name
            checkpoint_config=CheckpointConfig(num_to_keep=2),
        ),
        torch_config=FSDPConfig()
    )

    result = trainer.fit()
