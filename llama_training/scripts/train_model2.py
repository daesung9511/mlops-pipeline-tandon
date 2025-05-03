import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    BitsAndBytesConfig
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

# --- Global tokenizer 선언 ---
tokenizer = None

# --- Preprocess 함수 ---
def preprocess(batch):
    queries = []
    answers = []

    for example in batch['general_query_list']:
        if example is not None:
            for item in example:
                if 'query' in item and 'answer' in item:
                    queries.append(item['query'])
                    answers.append(item['answer'])

    for example in batch['specific_query_list']:
        if example is not None:
            for item in example:
                if 'query' in item and 'answer' in item:
                    queries.append(item['query'])
                    answers.append(item['answer'])

    if len(queries) > 0 and len(answers) > 0:
        model_inputs = tokenizer(
            queries,
            text_target=answers,
            max_length=512,
            truncation=True,
            padding="max_length",    # 여기가 pad_token 필요했던 부분!
        )
        return model_inputs
    else:
        return {'input_ids': [], 'attention_mask': [], 'labels': []}

# --- Main 함수 ---
def main():
    global tokenizer

    print("Loading dataset...")
    dataset = load_dataset('json', data_files={
        'train': './llama_training/data/QMSum-main/data/ALL/jsonl/train.jsonl',
        'validation': './llama_training/data/QMSum-main/data/ALL/jsonl/val.jsonl',
        'test': './llama_training/data/QMSum-main/data/ALL/jsonl/test.jsonl'
    })

    print("Loading model and tokenizer (4bit)...")
    model_name = "meta-llama/Llama-2-7b-chat-hf"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    # ✨ pad_token 설정 추가!
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
    )

    # PEFT 설정
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    print("Tokenizing...")
    tokenized_dataset = dataset.map(
        preprocess,
        batched=True,
        remove_columns=dataset['train'].column_names,
        num_proc=1
    )

    print("Setting up Trainer...")
    training_args = TrainingArguments(
        output_dir="./llama_training/outputs",
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        num_train_epochs=3,
        logging_dir="./llama_training/logs",
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=50,
        save_steps=100,
        save_total_limit=2,
        learning_rate=2e-4,
        bf16=True,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset['train'],
        eval_dataset=tokenized_dataset['validation'],
        tokenizer=tokenizer,
    )

    print("Starting training...")
    trainer.train()

# --- 실행 ---
if __name__ == "__main__":
    main()

