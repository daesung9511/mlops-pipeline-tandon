import torch
from transformers import LlamaTokenizer, LlamaForCausalLM, Trainer, TrainingArguments
from datasets import load_dataset

def main():
    print("Loading dataset...")
    dataset = load_dataset('json', data_files={
        'train': './llama_training/data/QMSum-main/data/ALL/jsonl/train.jsonl',
        'validation': './llama_training/data/QMSum-main/data/ALL/jsonl/val.jsonl',
        'test': './llama_training/data/QMSum-main/data/ALL/jsonl/test.jsonl'
    })

    print("Loading model and tokenizer...")
    model_name = "meta-llama/Llama-2-7b-chat-hf"
    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    model = LlamaForCausalLM.from_pretrained(model_name)

    # pad_token 설정
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
        model_inputs = tokenizer(inputs, text_target=targets, max_length=512, truncation=True, padding="max_length")
        return model_inputs

    tokenized_dataset = dataset.map(preprocess, batched=True, remove_columns=dataset['train'].column_names)

    print("Setting up Trainer...")
    training_args = TrainingArguments(
        output_dir="./llama_training/results",
        per_device_train_batch_size=1,   # ✅ 수정: 메모리 절약을 위해 1
        per_device_eval_batch_size=1,    # ✅ 수정: 메모리 절약을 위해 1
        num_train_epochs=3,
        learning_rate=2e-5,
        weight_decay=0.01,
        logging_dir="./llama_training/logs",
        bf16=True,  # A100 GPU용 최적화
        report_to="none",
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

    print("Saving model...")
    model.save_pretrained("./llama_training/models/llama-2-7b-checkpoint")
    tokenizer.save_pretrained("./llama_training/models/llama-2-7b-checkpoint")

if __name__ == "__main__":
    main()
