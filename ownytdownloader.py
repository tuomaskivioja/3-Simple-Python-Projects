from pytube import YouTube, Playlist
import os
import sys

def progress_function(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining 
    percentage_of_completion = bytes_downloaded / total_size * 100
    sys.stdout.write(f"\rDownloading: {percentage_of_completion:.2f}%")
    sys.stdout.flush()

def download_video(yt, path):
    yt.register_on_progress_callback(progress_function)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    stream.download(output_path=path)
    print(f"\nDownloaded {yt.title} to {path}")

def download_audio(yt, path):
    yt.register_on_progress_callback(progress_function)
    stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    stream.download(output_path=path, filename=f"{yt.title}.mp3")
    print(f"\nDownloaded audio of {yt.title} to {path}")

def download_playlist(url, path):
    pl = Playlist(url)
    total_videos = len(pl.video_urls)
    print(f"Total videos in the playlist: {total_videos}")

    downloaded_videos = 0
    for video_url in pl.video_urls:
        yt = YouTube(video_url)
        download_video(yt, path)
        downloaded_videos += 1
        print(f"Downloaded {downloaded_videos}/{total_videos} videos from playlist")

def main():
    url = input("Enter the YouTube URL: ")
    download_choice = input("Download Video or Audio (V/A): ").lower()
    is_playlist = 'playlist' in url

    if is_playlist:
        playlist_path = input("Enter the folder name for the playlist: ")
        path = os.path.join("D:/Videos/Playlists", playlist_path)
        os.makedirs(path, exist_ok=True)
        download_playlist(url, path)
    else:
        yt = YouTube(url)
        if download_choice == 'v':
            video_path = 'D:/Videos' 
            os.makedirs(video_path, exist_ok=True)
            download_video(yt, video_path)
        elif download_choice == 'a':
            audio_path = 'D:/Music'
            os.makedirs(audio_path, exist_ok=True)
            download_audio(yt, audio_path)

if __name__ == "__main__":
    main()
