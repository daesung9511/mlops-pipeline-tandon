# -*- coding: utf-8 -*-
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
)

# Check for CUDA
os.environ["LD_LIBRARY_PATH"] = "/usr/local/cuda/lib64:" + os.environ.get("LD_LIBRARY_PATH", "")
if not torch.cuda.is_available():
    raise RuntimeError("CUDA is not available.")

tokenizer = None

# Preprocessing function
def preprocess(example):
    prompt = f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Output:"
    return tokenizer(
        prompt,
        text_target=example['output'],
        padding="max_length",
        truncation=True,
        max_length=1024
    )

def main():
    global tokenizer

    print("[1/6] Loading dataset...")
    dataset = load_dataset(
        'json',
        data_files={
            'train': '/workspace/llama_training/data/train.jsonl',
            'validation': '/workspace/llama_training/data/val.jsonl'
        }
    )

    print("[2/6] Loading model and tokenizer...")
    model_name = "meta-llama/Llama-2-7b-chat-hf"
    hf_token = os.environ.get("HUGGINGFACE_TOKEN")

    tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        token=hf_token
    )

    print("[3/6] Preprocessing dataset...")
    tokenized_dataset = dataset.map(preprocess, batched=False)

    print("[4/6] Setting up Trainer...")
    training_args = TrainingArguments(
        output_dir="/workspace/llama_training/results",
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        num_train_epochs=3,
        learning_rate=2e-5,
        bf16=True,
        logging_dir="/workspace/llama_training/logs",
        logging_steps=10,
        save_strategy="steps",
        save_steps=200,
        evaluation_strategy="steps",
        eval_steps=200,
        save_total_limit=2,
        # Commented out to avoid OOM on evaluation
        # load_best_model_at_end=True,
        # metric_for_best_model="loss",
        # greater_is_better=False,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset['train'],
        eval_dataset=tokenized_dataset['validation'],
        tokenizer=tokenizer,
    )

    print("[5/6] Starting training...")
    trainer.train()

    print("[6/6] Saving final model...")
    trainer.save_model("/workspace/llama_training/models/final_model")
    trainer.save_state()

if __name__ == "__main__":
    main()

