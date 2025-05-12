from transformers import BartTokenizer, BartForConditionalGeneration
import torch

# 1. Load model and tokenizer from the best checkpoint
model_dir = "/workspace/results/checkpoint-1644"
tokenizer = BartTokenizer.from_pretrained(model_dir)
model = BartForConditionalGeneration.from_pretrained(model_dir)
model.eval()

# 2. Sample input: query + meeting_transcripts
query = "What challenges did the team identify for international expansion?"

context = (
    "Speaker A: We’re seeing interest in Germany and Brazil.",
    "Speaker B: Localization and payment system integration will be tough.",
    "Speaker C: Do we have legal counsel familiar with EU privacy laws?",
    "Speaker A: Not yet, but we’re reaching out to a firm next week."
)


input_text = f"question: {query} context: {context}"
inputs = tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)

# 3. Generate summary
with torch.no_grad():
    summary_ids = model.generate(
        inputs["input_ids"],
        num_beams=4,
        no_repeat_ngram_size=3,
        min_length=30,
        max_length=128,
        early_stopping=True
    )

summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
print("\n📌 Summary:")
print(summary)
