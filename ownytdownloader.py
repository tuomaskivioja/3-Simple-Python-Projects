from pytube import YouTube, Playlist
import os
import subprocess
from tqdm import tqdm

def sanitize_filename(title):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        title = title.replace(char, '')
    return title

def download_video(yt, path):
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc='Downloading', ascii=True)

    def progress_function(stream, chunk, bytes_remaining):
        current = stream.filesize - bytes_remaining
        tqdm_instance.update(current - tqdm_instance.n)

    yt.register_on_progress_callback(progress_function)

    sanitized_title = sanitize_filename(yt.title)
    stream.download(output_path=path, filename=sanitized_title)
    tqdm_instance.close()
    print(f"\nDownloaded {sanitized_title} to {path}")
    
def download_audio(yt, path):
    stream = yt.streams.filter(only_audio=True, file_extension='mp3').order_by('abr').desc().first()

    if not stream:
        print("MP3 format not available. Downloading in best available audio format and converting to MP3.")
        stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        temp_filename = sanitize_filename(yt.title) + "." + stream.mime_type.split('/')[1]
        final_filename = sanitize_filename(yt.title) + ".mp3"

        tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc='Downloading', ascii=True)

        def progress_function(stream, chunk, bytes_remaining):
            current = stream.filesize - bytes_remaining
            tqdm_instance.update(current - tqdm_instance.n)

        yt.register_on_progress_callback(progress_function)
        stream.download(output_path=path, filename=temp_filename)
        tqdm_instance.close()

        # Specify the full path to your FFmpeg executable here
        ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg.exe'
        subprocess.run([ffmpeg_path, '-i', os.path.join(path, temp_filename), os.path.join(path, final_filename)])
        os.remove(os.path.join(path, temp_filename))
        print(f"\nConverted to MP3 and saved as {final_filename} in {path}")
    else:
        tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc='Downloading', ascii=True)

        def progress_function(stream, chunk, bytes_remaining):
            current = stream.filesize - bytes_remaining
            tqdm_instance.update(current - tqdm_instance.n)

        yt.register_on_progress_callback(progress_function)
        sanitized_title = sanitize_filename(yt.title) + ".mp3"
        stream.download(output_path=path, filename=sanitized_title)
        tqdm_instance.close()
        print(f"\nDownloaded {sanitized_title} to {path}")

def download_playlist(url, path):
    pl = Playlist(url)
    print(f"\nPlaylist details: ")
    print(f"Playlist name: {pl.title}")
    print(f"Total videos in the playlist: {len(pl.video_urls)}")

    for index, video_url in enumerate(pl.video_urls, start=1):
        yt = YouTube(video_url)
        print(f"\nDownloading video {index} of {len(pl.video_urls)}: {yt.title}")
        download_video(yt, path)

def main():
    url = input("Enter the YouTube URL: ")
    download_choice = input("Download Video or Audio (V/A): ").lower()
    is_playlist = 'playlist' in url

    if is_playlist:
        playlist_path = input("\nEnter the folder name for the playlist: ")
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
