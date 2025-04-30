import argparse
import whisper

def main():
    parser = argparse.ArgumentParser(description="Download a Whisper model to a custom directory.")
    parser.add_argument('--save_dir', type=str, required=True, help='Directory to save the Whisper model')
    parser.add_argument('--model_size', type=str, required=True, help='Size of the Whisper model (e.g., tiny, base, small, medium, large, turbo)')
    args = parser.parse_args()

    # Load the model, which will download it to your specified directory if not present
    whisper_model = whisper.load_model(args.model_size, download_root=args.save_dir)
    print(f"Model '{args.model_size}' downloaded to '{args.save_dir}'.")

if __name__ == '__main__':
    main()

