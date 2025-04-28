import whisper
import subprocess
from whisper.utils import get_writer


def trim_audio_ffmpeg(input_path, output_path, end_min=5):
    """
    Trim using FFmpeg (faster, no re-encoding).

    Args:
        input_path (str): Input audio path
        output_path (str): Output audio path
        end_min (int): End time in minutes
    """
    end_time = end_min * 60  # Convert to seconds
    command = [
        "ffmpeg",
        "-i", input_path,
        "-ss", "0",          # Start at 0 seconds
        "-to", str(end_time),
        "-c", "copy",        # Copy stream (no re-encoding)
        output_path
    ]
    subprocess.run(command, check=True)


def run_whisper_diarization(audio_file_path, output_file_name):
    result = whisper_model.transcribe(audio_file_path, word_timestamps=True)

    # Save results in VTT format with timestamps
    writer = get_writer("vtt", ".")
    writer(result, f"{output_file_name}.vtt")

    return result


if __name__ == "__main__":
    # Load the Whisper model
    whisper_model = whisper.load_model("base")

    # Example usage
    youtube_url = "https://www.youtube.com/watch?v=example_video_id"
    output_audio_path = "audio_30min_ffmpeg.mp3"
    end_min = 30

    # Download and trim the audio
    download_audio(youtube_url, output_audio_path, end_min)
    # Trim the audio using FFmpeg
    trimmed_audio_path = "trimmed_audio.mp3"
    trim_audio_ffmpeg(output_audio_path, trimmed_audio_path, end_min)
    # Run Whisper diarization
    output_file_name = "diarization_output"
    run_whisper_diarization(trimmed_audio_path, output_file_name)
    # Clean up
    