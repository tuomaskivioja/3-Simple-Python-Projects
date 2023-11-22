from pytube import YouTube, Playlist, exceptions
import os
import subprocess
from tqdm import tqdm
import datetime

def log_download_details(url, status, log_dir, error_msg=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] URL: {url}, Status: {status}"

    if error_msg:
        log_message += f", Error: {error_msg}"

    try:
        # Create directory if it does not exist
        os.makedirs(log_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating log directory: {e}")
        return  # Exit the function if directory creation fails

    log_file_path = os.path.join(log_dir, "download_history.log")
    with open(log_file_path, "a") as log_file:
        log_file.write(log_message + "\n")

# Function to remove invalid characters from filenames
def sanitize_filename(title):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        title = title.replace(char, '')
    return title

# Function to check the integrity of a downloaded file using FFmpeg
def check_file_integrity(file_path, ffmpeg_path='C:\\ffmpeg\\bin\\ffmpeg.exe'):
    try:
        print(f"\nChecking file integrity for {file_path}...")
        result = subprocess.run(
            [ffmpeg_path, '-v', 'error', '-i', file_path, '-f', 'null', '-'],
            check=True, text=True, stderr=subprocess.PIPE
        )
        if result.stderr:
            print(f"File {file_path} might be corrupted. Errors: {result.stderr}")
        else:
            print(f"File {file_path} is not corrupted.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while checking {file_path}: {e.stderr}")

# Function to ensure the correct file extension is present
def correct_file_extension(file_path, desired_extension):
    if not os.path.splitext(file_path)[1]:  # No extension
        new_file_path = f"{file_path}.{desired_extension}"
        os.rename(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
        return new_file_path
    return file_path

# Function to download the highest quality video from a YouTube link
def download_highest_quality_video(yt, path, log_dir):
    try:
        # Log the start of download
        log_download_details(yt.watch_url, "Started", log_dir)
        # Separate streams for video and audio
        video_stream = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc().first()
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

        # Paths for video and audio files
        video_path = os.path.join(path, sanitize_filename(yt.title) + '_video.mp4')
        audio_path = os.path.join(path, sanitize_filename(yt.title) + '_audio.mp4')

        # Download video with progress bar
        download_with_progress(video_stream, video_path, yt)

        # Download audio with progress bar
        download_with_progress(audio_stream, audio_path, yt)

        # Merge video and audio files
        merge_files(video_path, audio_path, os.path.join(path, sanitize_filename(yt.title) + '.mp4'))

        # Delete the separate video and audio files
        os.remove(video_path)
        os.remove(audio_path)

        # Correct file extension if necessary and check file integrity
        final_path = correct_file_extension(os.path.join(path, sanitize_filename(yt.title) + '.mp4'), "mp4")
        check_file_integrity(final_path)
        # Log successful download
        log_download_details(yt.watch_url, "Success", log_dir)
    except exceptions.PytubeError as e:
        print(f"An error occurred while downloading the video. Please check your network connection and try again. Details: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error in processing video/audio: {e}")
    except Exception as e:
        # Log failed download
        log_download_details(yt.watch_url, "Failed", log_dir, str(e))
        print(f"Unexpected error: {e}")

# Helper function to download with a progress bar
def download_with_progress(stream, file_path, yt):
    tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, desc=f'Downloading {os.path.basename(file_path)}', ascii=True)

    def progress_function(stream, chunk, bytes_remaining):
        current = stream.filesize - bytes_remaining
        tqdm_instance.update(current - tqdm_instance.n)

    yt.register_on_progress_callback(progress_function)
    stream.download(filename=file_path)
    tqdm_instance.close()

# Function to merge video and audio files using FFmpeg
def merge_files(video_path, audio_path, output_path):
    ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg.exe'
    subprocess.run([ffmpeg_path, '-i', video_path, '-i', audio_path, '-c', 'copy', output_path])

# Function to download only audio from a YouTube link
def download_audio(yt, path, log_dir):
    try:
        # Log the start of download
        log_download_details(yt.watch_url, "Started", log_dir)
        # Select the best audio stream
        stream = yt.streams.filter(only_audio=True, file_extension='mp3').order_by('abr').desc().first()

        # Sanitize and set up file path
        sanitized_title = sanitize_filename(yt.title)
        final_filename = f"{sanitized_title}.mp3"
        file_path = os.path.join(path, final_filename)

        # Check if file already exists
        if os.path.exists(file_path):
            user_input = input(f"{final_filename} already exists. Would you like to skip downloading this file? Enter 'Y' for Yes or 'N' for No: ").lower()
            if user_input == 'y':
                print(f"Skipping {final_filename}...")
                return
            else:
                # Append a number to the filename to avoid conflict
                counter = 1
                new_filename = f"{sanitized_title} ({counter}).mp3"
                new_file_path = os.path.join(path, new_filename)
                while os.path.exists(new_file_path):
                    counter += 1
                    new_filename = f"{sanitized_title} ({counter}).mp3"
                    new_file_path = os.path.join(path, new_filename)
            
                final_filename = new_filename
                file_path = new_file_path
                print(f"Redownloading as {final_filename}...")

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
        # Log successful download
        log_download_details(yt.watch_url, "Success", log_dir)
    except exceptions.PytubeError as e:
        print(f"An error occurred while downloading audio. Please check your network connection and try again. Details: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error in processing audio: {e}")
    except Exception as e:
        # Log failed download
        log_download_details(yt.watch_url, "Failed", log_dir, str(e))
        print(f"Unexpected error: {e}")

# Function to download a complete YouTube playlist
def download_playlist(url, path, download_choice):
    try:
        pl = Playlist(url)
        print(f"\nPlaylist details: ")
        print(f"Playlist name: {pl.title}")
        print(f"Total videos in the playlist: {len(pl.video_urls)}")

        # Loop through each video in the playlist and download based on user choice
        for index, video_url in enumerate(pl.video_urls, start=1):
            yt = YouTube(video_url)
            print(f"\nDownloading {('audio' if download_choice == 'a' else 'video')} {index} of {len(pl.video_urls)}: {yt.title}")
            if download_choice == 'v':
                download_highest_quality_video(yt, path)
            elif download_choice == 'a':
                download_audio(yt, path)
    except exceptions.PytubeError as e:
        print(f"An error occurred while downloading the playlist. Please check your network connection and try again. Details: {e}")
    except Exception as e:
        print(f"Unexpected error in playlist download: {e}")

# Main function to handle user input and start the download process
def main():
    try:
        log_dir = "D:\\logs"
        url = input("Please enter the full YouTube URL (video or playlist): ")
        download_choice = input("Would you like to download Video or Audio? Please enter 'V' for Video or 'A' for Audio: ").lower()
        is_playlist = 'playlist' in url
        print(f"Default log file directory is '{log_dir}'.")

        # Handling downloads for playlists and individual videos or audio
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
                download_highest_quality_video(yt, video_path, log_dir)
            elif download_choice == 'a':
                audio_path = 'D:/Music'
                os.makedirs(audio_path, exist_ok=True)
                download_audio(yt, audio_path, log_dir)
    except ValueError as e:
        print(f"Invalid input: {e}")
    except Exception as e:
        log_download_details(url, "Failed", log_dir, str(e))
        print(f"Unexpected error in main: {e}")
    except KeyboardInterrupt:
        log_download_details(url, "Interrupted", "User stopped the program")
        print("\nProgram stopped by the user. Exiting now...")  

if __name__ == "__main__":
    main()
