import torch
from torch.utils.data import Dataset

class UNQADataset(Dataset):
    def __init__(self, json_path, tokenizer):
        import json
        with open(json_path, "r") as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        enc = self.tokenizer(
            item["question"],
            item["context"],
            truncation=True,
            padding="max_length",
            max_length=128,
            return_tensors="pt"
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "clip": torch.tensor(item["clip_embed"], dtype=torch.float32),
            "label": torch.tensor(item["is_relevant"], dtype=torch.long),  # ✅ 핵심 수정!
        }
