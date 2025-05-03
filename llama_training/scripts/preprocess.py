from datasets import load_dataset
import os
import json

def load_and_save_dataset():
    # 데이터 파일 경로
    data_files = {
        'train': '/workspace/llama_training/data/QMSum-main/data/ALL/jsonl/train.jsonl',
        'validation': '/workspace/llama_training/data/QMSum-main/data/ALL/jsonl/val.jsonl',
        'test': '/workspace/llama_training/data/QMSum-main/data/ALL/jsonl/test.jsonl'
    }

    # 데이터셋 로드
    dataset = load_dataset('json', data_files=data_files)

    # 불러온 train 데이터 출력
    print("First training sample:")
    print(dataset['train'][0])

    # 저장할 디렉토리 생성
    os.makedirs('/workspace/llama_training/data', exist_ok=True)

    # train.jsonl 저장
    output_train_path = '/workspace/llama_training/data/train.jsonl'
    with open(output_train_path, 'w') as f:
        for sample in dataset['train']:
            f.write(json.dumps(sample) + '\n')

    print(f"\nSaved {len(dataset['train'])} training samples to {output_train_path}")

def main():
    load_and_save_dataset()

if __name__ == "__main__":
    main()

