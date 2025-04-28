from ray.train.torch import TorchTrainer
from ray.train import ScalingConfig
from train_job import train_loop
import yaml

if __name__ == "__main__":
    config = yaml.safe_load(open("config/ray_train.yaml"))
    trainer = TorchTrainer(
        train_loop_per_worker=train_loop,
        train_loop_config=config,
        scaling_config=ScalingConfig(num_workers=1, use_gpu=True),
    )
    trainer.fit()
