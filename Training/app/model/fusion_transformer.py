import torch
import torch.nn as nn
from transformers import AutoModel

class MultimodalFusion(nn.Module):
    def __init__(self, text_model_name="bert-base-uncased", fusion_dim=256):
        super().__init__()
        self.text_model = AutoModel.from_pretrained(text_model_name)
        self.text_proj = nn.Linear(self.text_model.config.hidden_size, fusion_dim)
        self.clip_proj = nn.Linear(512, fusion_dim)
        self.classifier = nn.Sequential(
            nn.ReLU(),
            nn.Linear(fusion_dim * 2, 2)
        )

    def forward(self, clip, input_ids, attention_mask):
        text_out = self.text_model(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0, :]
        text_feat = self.text_proj(text_out)
        clip_feat = self.clip_proj(clip)
        combined = torch.cat([text_feat, clip_feat], dim=1)
        return self.classifier(combined)
