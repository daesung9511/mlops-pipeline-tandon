import yt_dlp
import subprocess
import argparse

'''
Example command:
python3 process_yt_video.py --video_url https://www.youtube.com/watch?v=6U0a36WSirA --audio_save_path audio1.mp3 --video_save_path video1.mp4 --audio_len 1
'''

def download_video(youtube_url, output_video_path):
    """
    Downloads the full video from a YouTube URL to a specified file path.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{output_video_path}',
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])


def extract_audio_from_video(video_file_path, output_audio_path, len_min):
    """
    Extracts the first N minutes of audio from a local video file and saves as MP3.
    """
    duration = len_min * 60  # seconds
    # Ensure output ends with .mp3
    if not output_audio_path.endswith('.mp3'):
        output_audio_path += '.mp3'

    command = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-i', video_file_path,
        '-t', str(duration),  # Duration in seconds
        '-vn',  # No video
        '-acodec', 'libmp3lame',
        '-ab', '128k',
        output_audio_path
    ]
    subprocess.run(command, check=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download a YouTube video and extract audio from it."
    )
    parser.add_argument('--video_url', type=str, required=True, help='YouTube video URL')
    parser.add_argument('--audio_save_path', type=str, required=True, help='Path to save the extracted audio file (e.g., audio1.mp3)')
    parser.add_argument('--video_save_path', type=str, required=True, help='Path to save the downloaded video file (e.g., video1.mp4)')
    parser.add_argument('--audio_len', type=int, required=True, help='Length of audio to extract in minutes')
    args = parser.parse_args()

    # Call your video download function
    download_video(args.video_url, args.video_save_path)

    # Call your audio extraction function (from local file)
    extract_audio_from_video(video_full_path, args.audio_save_path, args.audio_len)
