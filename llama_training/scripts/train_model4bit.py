import torch
from transformers import (
    LlamaTokenizer,
    LlamaForCausalLM,
    Trainer,
    TrainingArguments,
    BitsAndBytesConfig,
)
from datasets import load_dataset

def main():
    print("Loading dataset...")
    dataset = load_dataset('json', data_files={
        'train': './llama_training/data/QMSum-main/data/ALL/jsonl/train.jsonl',
        'validation': './llama_training/data/QMSum-main/data/ALL/jsonl/val.jsonl',
        'test': './llama_training/data/QMSum-main/data/ALL/jsonl/test.jsonl'
    })

    print("Loading model and tokenizer (4bit)...")
    model_name = "meta-llama/Llama-2-7b-chat-hf"

    tokenizer = LlamaTokenizer.from_pretrained(model_name)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",           # 4bit 타입 (nf4: best practice)
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,  # A100이면 bf16 좋음
    )

    model = LlamaForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto"   # GPU 자동 인식
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizing...")
    def preprocess(examples):
        inputs = []
        targets = []
        for general_query_list in examples["general_query_list"]:
            if isinstance(general_query_list, list):
                for qa_pair in general_query_list:
                    inputs.append(qa_pair["query"])
                    targets.append(qa_pair["answer"])
        model_inputs = tokenizer(inputs, text_target=targets, max_length=512, truncation=True)
        return model_inputs

    tokenized_dataset = dataset.map(preprocess, batched=True, remove_columns=dataset['train'].column_names)

    print("Setting up Trainer...")
    training_args = TrainingArguments(
        output_dir="./llama_training/results",
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=500,
        save_total_limit=2,
        logging_dir="./llama_training/logs",
        learning_rate=2e-5,
        per_device_train_batch_size=2,     # 4bit니까 2도 가능
        per_device_eval_batch_size=2,
        num_train_epochs=3,
        weight_decay=0.01,
        bf16=True,                         # A100이니까 bf16
        gradient_checkpointing=True,       # 메모리 절약
        report_to="none",                  # MLflow 안씀
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
        tokenizer=tokenizer,
    )

    print("Starting training...")
    trainer.train()

if __name__ == "__main__":
    main()

