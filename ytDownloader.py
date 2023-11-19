from pytube import YouTube, Playlist
from tqdm import tqdm
import os

def progress_function(stream, chunk, bytes_remaining):
    current = ((stream.filesize - bytes_remaining) / stream.filesize)
    percent = ('{0:.1f}').format(current * 100)
    progress = int(50 * current)
    status = '█' * progress + '-' * (50 - progress)
    print(f'\r|{status}| {percent}%', end='')

def update_playlist_progress(completed, total):
    percent = (completed / total) * 100
    print(f"\nPlaylist Download Progress: {completed}/{total} videos ({percent:.1f}%)")

def download_video(url, path, audio_only=False):
    yt = YouTube(url)
    yt.register_on_progress_callback(progress_function)
    stream = yt.streams.filter(only_audio=audio_only).get_highest_resolution()
    print(f"Downloading: {yt.title}")
    stream.download(output_path=path)
    print(f"\nDownload complete: {yt.title}")

def download_playlist(url, directory, audio_only=False):
    playlist = Playlist(url)
    path = os.path.join("D:/Videos/Playlists", directory)
    os.makedirs(path, exist_ok=True)
    total_videos = len(playlist.video_urls)
    completed_videos = 0

    print(f"Downloading playlist: {playlist.title}")
    for video in playlist.videos:
        download_video(video.watch_url, path, audio_only)
        completed_videos += 1
        update_playlist_progress(completed_videos, total_videos)
    print(f"Playlist download complete: {playlist.title}")

def main():
    url = input("Enter the YouTube URL: ")
    audio_or_video = input("Download audio only? (y/n): ").lower() == 'y'

    if 'playlist?list' in url:
        directory = input("Enter Playlist folder name: ")
        download_playlist(url, directory, audio_or_video)
    else:
        path = 'D:/Music' if audio_or_video else 'D:/Videos'
        download_video(url, path, audio_or_video)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")

