# evaluation.py
import json
from tqdm import tqdm
from transformers import BartTokenizer, BartForConditionalGeneration
import torch
import os

# Paths
MODEL_PATH = "/workspace/results/checkpoint-1644"  # <- 마지막 체크포인트 폴더로 수정!
DATA_PATH = "/workspace/llama_training/data/test.jsonl"
OUTPUT_PATH = "/workspace/llama_training/results/predictions.jsonl"

# Load model & tokenizer
tokenizer = BartTokenizer.from_pretrained(MODEL_PATH)
model = BartForConditionalGeneration.from_pretrained(MODEL_PATH)
model.to("cuda" if torch.cuda.is_available() else "cpu")
model.eval()

# Load dataset
with open(DATA_PATH, "r") as f:
    dataset = [json.loads(line.strip()) for line in f]

# Run evaluation
predictions = []
for example in tqdm(dataset):
    prompt = example["prompt"]
    input_ids = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(model.device)
    with torch.no_grad():
        outputs = model.generate(input_ids, max_new_tokens=128)
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    predictions.append({"prompt": prompt, "prediction": decoded})

# Save results
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    for p in predictions:
        f.write(json.dumps(p) + "\n")

print(f"✅ Evaluation completed. Results saved to {OUTPUT_PATH}")
