#!/bin/bash
bash infra/run_mlflow_server.sh &
ray start --head --num-cpus=8 --num-gpus=1
python train/train_ray.py --config config/ray_train.yaml
