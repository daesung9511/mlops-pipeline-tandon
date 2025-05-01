import json
from tqdm import tqdm
import torch
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge
from transformers import LlamaTokenizer, LlamaForCausalLM
from peft import PeftModel

def generate_response(model, tokenizer, prompt):
    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def evaluate(model_path, data_path, base_model_path="meta-llama/Llama-2-7b-chat-hf"):
    print("🔹 모델 및 토크나이저 로드 중...")
    tokenizer = LlamaTokenizer.from_pretrained(base_model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = LlamaForCausalLM.from_pretrained(base_model_path, device_map="auto")
    model = PeftModel.from_pretrained(base_model, model_path).eval()

    print("🔹 평가용 데이터 로드 중...")
    with open(data_path, 'r') as f:
        data = [json.loads(line) for line in f]

    bleu_scores, rouge_scores = [], []
    rouge = Rouge()

    print("🔹 응답 생성 및 평가 중...")
    for item in tqdm(data):
        prompt = item["instruction"] + " " + item["input"]
        target = item["output"]
        prediction = generate_response(model, tokenizer, prompt)

        bleu = sentence_bleu([target.split()], prediction.split())
        rouge_score = rouge.get_scores(prediction, target)[0]['rouge-l']['f']

        bleu_scores.append(bleu)
        rouge_scores.append(rouge_score)

        print(f"\n📌 질문: {item['instruction']}")
        print(f"🔸 모델 응답: {prediction}")
        print(f"🔹 정답: {target}")

    print("\n📊 평가 결과:")
    print(f"🔹 평균 BLEU: {sum(bleu_scores)/len(bleu_scores):.4f}")
    print(f"🔹 평균 ROUGE-L F1: {sum(rouge_scores)/len(rouge_scores):.4f}")

if __name__ == "__main__":
    evaluate(
        model_path="/workspace/llama_training/models/final_model",
        data_path="/workspace/llama_training/data/test.jsonl"
    )
