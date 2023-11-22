from pytube import YouTube, Playlist
import os
import subprocess
from tqdm import tqdm

def sanitize_filename(title):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        title = title.replace(char, '')
    return title

def check_file_integrity(file_path, ffmpeg_path='C:\\ffmpeg\\bin\\ffmpeg.exe'):
    try:
        print(f"\nChecking file integrity for {file_path}...")
        result = subprocess.run(
            [ffmpeg_path, '-v', 'error', '-i', file_path, '-f', 'null', '-'],
            check=True, text=True, stderr=subprocess.PIPE
        )
        if result.stderr:
            print(f"\nFile {file_path} might be corrupted. Errors: {result.stderr}")
        else:
            print(f"\nFile {file_path} is not corrupted.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while checking {file_path}: {e.stderr}")

def correct_file_extension(file_path, desired_extension):
    if not os.path.splitext(file_path)[1]:  # No extension
        new_file_path = f"{file_path}.{desired_extension}"
        os.rename(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
        return new_file_path
    return file_path

def download_video(yt, path):
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc='Downloading', ascii=True)

    def progress_function(stream, chunk, bytes_remaining):
        current = stream.filesize - bytes_remaining
        tqdm_instance.update(current - tqdm_instance.n)

    yt.register_on_progress_callback(progress_function)

    sanitized_title = sanitize_filename(yt.title)
    file_path = os.path.join(path, sanitized_title)
    stream.download(output_path=path, filename=sanitized_title)
    tqdm_instance.close()
    print(f"\nDownloaded {sanitized_title} to {path}")

    # Correct file extension if necessary
    file_path = correct_file_extension(file_path, "mp4")

    # Check file integrity
    check_file_integrity(file_path)
    
def download_audio(yt, path):
    stream = yt.streams.filter(only_audio=True, file_extension='mp3').order_by('abr').desc().first()

    sanitized_title = sanitize_filename(yt.title)
    final_filename = f"{sanitized_title}.mp3"
    file_path = os.path.join(path, final_filename)

    if not stream:
        print("MP3 format not available. Downloading in best available audio format and converting to MP3.")
        # Select the best audio stream regardless of format
        stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        temp_filename = f"{sanitized_title}.{stream.mime_type.split('/')[1]}"
        temp_file_path = os.path.join(path, temp_filename)

        tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc='Downloading', ascii=True)

        def progress_function(stream, chunk, bytes_remaining):
            current = stream.filesize - bytes_remaining
            tqdm_instance.update(current - tqdm_instance.n)

        yt.register_on_progress_callback(progress_function)
        stream.download(output_path=path, filename=temp_filename)
        tqdm_instance.close()

        # Convert to MP3
        ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg.exe'
        subprocess.run([ffmpeg_path, '-i', temp_file_path, file_path])
        os.remove(temp_file_path)
        print(f"\nConverted to MP3 and saved as {final_filename} in {path}")
    else:
        tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc='Downloading', ascii=True)

        def progress_function(stream, chunk, bytes_remaining):
            current = stream.filesize - bytes_remaining
            tqdm_instance.update(current - tqdm_instance.n)

        yt.register_on_progress_callback(progress_function)
        stream.download(output_path=path, filename=final_filename)
        tqdm_instance.close()
        print(f"\nDownloaded {final_filename} to {path}")

    # Correct file extension if necessary
    file_path = correct_file_extension(file_path, "mp3")

    # Check file integrity
    check_file_integrity(file_path)

def download_playlist(url, path, download_choice):
    pl = Playlist(url)
    print(f"\nPlaylist details: ")
    print(f"Playlist name: {pl.title}")
    print(f"Total videos in the playlist: {len(pl.video_urls)}")

    for index, video_url in enumerate(pl.video_urls, start=1):
        yt = YouTube(video_url)
        print(f"\nDownloading {('audio' if download_choice == 'a' else 'video')} {index} of {len(pl.video_urls)}: {yt.title}")
        if download_choice == 'v':
            download_video(yt, path)
        elif download_choice == 'a':
            download_audio(yt, path)

def main():
    url = input("Enter the YouTube URL: ")
    download_choice = input("Download Video or Audio (V/A): ").lower()
    is_playlist = 'playlist' in url

    if is_playlist:
        playlist_path = input("\nEnter the folder name for the playlist: ")
        path = os.path.join("D:/Videos/Playlists", playlist_path)
        os.makedirs(path, exist_ok=True)
        download_playlist(url, path, download_choice)  # Pass download_choice here
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
