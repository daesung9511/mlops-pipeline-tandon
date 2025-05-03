import argparse
from tqdm import tqdm
import yt_dlp

'''
You can now run the script as:
python3 download_audio.py --video_url https://www.youtube.com/watch?v=6U0a36WSirA --audio_output audio_output_1 --downloaded_video video1.mp4 --audio_length 1
'''

def download_audio_mp3(youtube_url, output_audio_path, len_min):
    """
    Downloads the first N minutes of audio from a YouTube video as an MP3.

    Args:
        youtube_url (str): The URL of the YouTube video.
        output_audio_path (str): The path to save the output MP3 file.
        len_min (int): Number of minutes to download from the start.
    """
    progress_bar = None

    def progress_hook(d):
        nonlocal progress_bar
        if d['status'] == 'downloading':
            if progress_bar is None:
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                progress_bar = tqdm(
                    total=total_bytes,
                    unit='B',
                    unit_scale=True,
                    desc='Downloading Audio',
                    dynamic_ncols=True,
                    leave=True,
                    mininterval=0.5,
                    miniters=max(1, int(total_bytes * 0.01)),
                    ascii=True,
                    position=0
                )
            progress_bar.update(d['downloaded_bytes'] - progress_bar.n)
        elif d['status'] == 'finished':
            if progress_bar:
                progress_bar.close()
                tqdm.write(f"Download completed: {d['filename']}")

    # Format N as zero-padded minutes (e.g., 5 -> '05:00')
    end_time = f"*{int(len_min):02d}:00"
    download_range = f"*00:00-{end_time}"

    ydl_opts = {
        'format': 'bestaudio[abr<=128]/worstaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'outtmpl': output_audio_path + '.%(ext)s',
        'progress_hooks': [progress_hook],
        'download_sections': [download_range],  # Use the dynamic section
        'force_keyframes_at_cuts': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

def download_video(youtube_url, output_video_path):
    """
    Downloads the full video from a YouTube URL to a specified file path.

    Args:
        youtube_url (str): The URL of the YouTube video.
        output_video_path (str): The path to save the downloaded video file.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_video_path,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download video and extract audio from YouTube.')
    parser.add_argument('--video_url', type=str, required=True, help='YouTube video URL')
    parser.add_argument('--audio_output', type=str, required=True, help='Output audio file name without extension')
    parser.add_argument('--downloaded_video', type=str, required=True, help='Output video file name with extension')
    parser.add_argument('--audio_length', type=int, default=1, help='Length of audio to extract in minutes')

    args = parser.parse_args()

    # Download the full video first
    download_video(args.video_url, args.downloaded_video)

    # Extract the first N minutes of audio from the video
    download_audio_mp3(args.video_url, args.audio_output, args.audio_length)
