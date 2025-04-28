import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from dataset.qa_dataset import UNQADataset
from model.fusion_transformer import MultimodalFusion
from ray import train
import mlflow

def train_loop(config):
    mlflow.set_tracking_uri(config["mlflow_uri"])
    mlflow.start_run()
    mlflow.log_params({k: config[k] for k in ["lr", "batch_size", "fusion_dim", "model_name"]})

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
    dataset = UNQADataset(config["data_path"], tokenizer)
    dataloader = DataLoader(dataset, batch_size=config["batch_size"], shuffle=True)

    model = MultimodalFusion(
        text_model_name=config["model_name"],
        fusion_dim=config["fusion_dim"]
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config["lr"]))
    criterion = nn.CrossEntropyLoss()

    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0
        for batch in dataloader:
            inputs = batch["input_ids"].to(device)
            masks = batch["attention_mask"].to(device)
            vision = batch["clip"].to(device)
            labels = batch["label"].to(device)

            # Debugging: Print a few values from the batch to ensure data integrity
            print("🟢 input_ids (first 10):", inputs[0][:10].tolist())
            print("🟡 clip mean:", vision[0].mean().item())
            print("🔵 label:", labels[0].item())

            outputs = model(vision, inputs, masks)
            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")
        mlflow.log_metric("loss", avg_loss, step=epoch)

    mlflow.end_run()
