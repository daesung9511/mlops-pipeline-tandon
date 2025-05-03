import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔹 응답 생성 중... (device: {device})")

model_path = "/workspace/llama_training/models/final_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", torch_dtype=torch.bfloat16)

prompt = """### Instruction:
Summarize the discussion about product appearance.

### Input:
Based on user feedback, 75% of participants found most remote controls ugly. The team discussed ways to make the product look fancy, such as using colorful options, but were concerned about increased production cost. The project manager emphasized keeping the design recognizable and affordable, and suggested offering multiple colors while maintaining the company image.

### Output:"""

inputs = tokenizer(prompt, return_tensors="pt").to(device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id
    )

decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\n=== 모델 응답 ===")
print(decoded)
