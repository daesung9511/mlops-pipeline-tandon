from transformers import BartTokenizer, BartForConditionalGeneration, Trainer, TrainingArguments
from datasets import load_dataset
import evaluate
import wandb
import numpy as np
wandb.login()
print(TrainingArguments.__module__)
# 1. Load preprocessed dataset
dataset = load_dataset("json", data_files={
    "train": "/workspace/QMSum-main/data/ALL/jsonl/train.jsonl",
    "validation": "/workspace/QMSum-main/data/ALL/jsonl/val.jsonl"
})

# 2. Load BART model
model_name = "facebook/bart-large"
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)

# 3. Preprocessing function
def preprocess_function(examples):
    inputs = ["question: " + q + " context: " + c for q, c in zip(examples["query"], examples["meeting_transcripts"])]
    model_inputs = tokenizer(inputs, max_length=1024, truncation=True, padding="max_length")

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(examples["answer"], max_length=256, truncation=True, padding="max_length")
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

# 4. Tokenize
tokenized_datasets = dataset.map(preprocess_function, batched=True)

# 5. Evaluation metric
#rouge = evaluate.load("rouge")

rouge = evaluate.load("rouge")
bleu = evaluate.load("bleu")
meteor = evaluate.load("meteor")
bertscore = evaluate.load("bertscore")

def compute_metrics(eval_preds):
    preds, labels = eval_preds

    # logits → 예측 token ID로 변환
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
    result_bleu = bleu.compute(predictions=decoded_preds, references=[[ref] for ref in decoded_labels])  # BLEU는 nested ref
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
# 6. TrainingArguments
training_args = TrainingArguments(
    output_dir="/workspace/results",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=5,
    weight_decay=0.01,
    save_total_limit=2,
    logging_dir="/workspace/logs",
    logging_steps=50,
    fp16=True,
    report_to="wandb",
    run_name="qmsum-bart(epoch5)",
    eval_accumulation_steps=2,
)

# 7. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

# 8. Train!
trainer.train()


