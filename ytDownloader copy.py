import os
import sys
import shutil
import subprocess
from pytube import YouTube, Playlist, exceptions
from tqdm import tqdm
import datetime
import time
import logging
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

# Constants for retry mechanism
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Function to fetch metadata (placeholder function)
def fetch_metadata(title):
    # Placeholder function to simulate metadata fetching
    return {
        "artist": "Unknown Artist",
        "album": "Unknown Album",
        "genre": "Unknown Genre"
    }

# Function to tag audio file with metadata
def tag_audio_file(file_path, metadata):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        for key in metadata:
            audio[key] = metadata[key]
        audio.save()
        print(f"Metadata tagged for {file_path}.")
    except Exception as e:
        print(f"Error tagging file {file_path}: {e}")

# Function to get FFmpeg path based on the operating system
def get_ffmpeg_path():
    ffmpeg_path = 'ffmpeg'
    if sys.platform == 'win32':
        ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg.exe'
    elif shutil.which(ffmpeg_path) is None:
        raise EnvironmentError("FFmpeg not found. Ensure it's installed and added to your PATH.")
    return ffmpeg_path

# Function to get default download and log directories
def get_default_directory(directory_type):
    if directory_type == 'download':
        if sys.platform == 'win32':
            return 'D:\\Downloads'
        else:
            return os.path.expanduser('~/Downloads')
    elif directory_type == 'log':
        if sys.platform == 'win32':
            return 'D:\\logs'
        else:
            return os.path.expanduser('~/logs')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Logging function to record download details
def log_download_details(url, status, log_dir, error_msg=None):
    """
    Log the details of a download attempt, including status and any error messages.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] URL: {url}, Status: {status}"

    if error_msg:
        detailed_error_msg = f"Error details: {error_msg}"
        log_message += f", {detailed_error_msg}"
    
    try:
        # Create directory if it does not exist
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "download_history.log"), "a") as log_file:
            log_file.write(log_message + "\n")
    except OSError as e:
        print(f"Error creating log directory: {e}")
        return  # Exit the function if directory creation fails
    except Exception as e:
        print(f"Error logging details: {e}")

# Function to handle batch download of videos or audios
def batch_download(urls, path, download_choice, log_dir):
    for url in urls:
        for attempt in range(MAX_RETRIES):
            try:
                yt = YouTube(url)
                if download_choice == 'v':
                    download_highest_quality_video(yt, path, log_dir)
                elif download_choice == 'a':
                    download_audio(yt, path, log_dir)
                break
            except exceptions.PytubeError as e:
                log_download_details(url, "Failed", log_dir, str(e))
                print(f"Pytube error during batch download: {e}")
            except Exception as e:
                log_download_details(url, "Failed", log_dir, str(e))
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print("Maximum retries reached. Moving to next URL.")

# Function to remove invalid characters from filenames
def sanitize_filename(title):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        title = title.replace(char, '')
    return title

# Function to check the integrity of a downloaded file using FFmpeg
def check_file_integrity(file_path):
    try:
        ffmpeg_path = get_ffmpeg_path()
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
    for attempt in range(MAX_RETRIES):
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
            break  # Exit loop if download is successful
        except exceptions.AgeRestrictedError as e:
            log_download_details(yt.watch_url, "Failed - Age Restricted", log_dir, str(e))
            print(f"Video is age restricted and cannot be downloaded: {e}")
        except exceptions.PytubeError as e:
            log_download_details(yt.watch_url, "Failed", log_dir, str(e))
            print(f"An error occurred while downloading the video. Please check your network connection and try again. Details: {e}")
        except subprocess.CalledProcessError as e:
            log_download_details(yt.watch_url, "Failed", log_dir, str(e))
            print(f"Error in processing video/audio: {e}")
        except Exception as e:
            log_download_details(yt.watch_url, "Failed - Attempt {attempt + 1}", log_dir, str(e))
            if attempt < MAX_RETRIES - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Maximum retries reached. Failed to download video.")

# Helper function to download with a progress bar
def download_with_progress(stream, file_path, yt):
    """
    Download a YouTube stream with an interactive progress bar showing detailed information.
    """
    logging.info(f"Starting download: {file_path}")

    tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, 
                         desc=f'Downloading {os.path.basename(file_path)}', 
                         ascii=True, miniters=1)

    last_time = time.time()
    last_bytes = 0

    def progress_function(stream, chunk, bytes_remaining):
        nonlocal last_time, last_bytes
        current_time = time.time()
        elapsed_time = current_time - last_time

        downloaded = stream.filesize - bytes_remaining
        tqdm_instance.update(downloaded - last_bytes)

        if elapsed_time > 0:
            # Calculate speed in KB/s
            speed = ((downloaded - last_bytes) / elapsed_time) / 1024
            eta = datetime.timedelta(seconds=int(bytes_remaining / (speed * 1024))) if speed > 0 else 'Unknown'
            eta_formatted = str(eta).split('.')[0] if isinstance(eta, datetime.timedelta) else eta
            tqdm_instance.set_postfix_str(f"Speed: {speed:.2f} KB/s, ETA: {eta_formatted}")

        last_time = current_time
        last_bytes = downloaded

    yt.register_on_progress_callback(progress_function)
    try:
        stream.download(filename=file_path)
        tqdm_instance.close()
        logging.info(f"Download completed: {file_path}")
    except Exception as e:
        logging.error(f"Error during download: {e}")
        tqdm_instance.close()

# Function to merge video and audio files using FFmpeg
def merge_files(video_path, audio_path, output_path):
    ffmpeg_path = get_ffmpeg_path()
    subprocess.run([ffmpeg_path, '-i', video_path, '-i', audio_path, '-c', 'copy', output_path])

# Function to download only audio from a YouTube link
def download_audio(yt, path, log_dir):
    for attempt in range(MAX_RETRIES):
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
                ffmpeg_path = get_ffmpeg_path()
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

            # Fetch and tag metadata
            metadata = fetch_metadata(yt.title)
            tag_audio_file(file_path, metadata)

            # Check file integrity
            check_file_integrity(file_path)
            # Log successful download
            log_download_details(yt.watch_url, "Success", log_dir)
            break  # Exit loop if download is successful
        except exceptions.PytubeError as e:
            print(f"An error occurred while downloading audio. Please check your network connection and try again. Details: {e}")
        except subprocess.CalledProcessError as e:
            print(f"Error in processing audio: {e}")
        except Exception as e:
            log_download_details(yt.watch_url, "Failed - Attempt {attempt + 1}", log_dir, str(e))
            if attempt < MAX_RETRIES - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Maximum retries reached. Failed to download audio.")

# Function to download a complete YouTube playlist with retries
def download_playlist(url, path, download_choice, log_dir, playlist_choice):
    try:
        pl = Playlist(url)
        print(f"\nPlaylist details: ")
        print(f"Playlist name: {pl.title}")
        print(f"Total videos in the playlist: {len(pl.video_urls)}")

        video_urls = pl.video_urls if playlist_choice == 'e' else select_videos(pl)

        if playlist_choice == 's':
            print("Videos to be downloaded:")
            for url in video_urls:
                yt = YouTube(url)
                print(yt.title)

        # Loop through each video in the playlist
        for index, video_url in enumerate(video_urls, start=1):
            for attempt in range(MAX_RETRIES):
                try:
                    yt = YouTube(video_url)
                    print(f"\nDownloading {('audio' if download_choice == 'a' else 'video')} {index} of {len(pl.video_urls)}: {yt.title}")
                    if download_choice == 'v':
                        download_highest_quality_video(yt, path, log_dir)
                    elif download_choice == 'a':
                        download_audio(yt, path, log_dir)
                    break  # Break out of retry loop if successful
                except Exception as e:
                    log_download_details(video_url, f"Failed - Attempt {attempt + 1}", log_dir, str(e))
                    if attempt < MAX_RETRIES - 1:
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                    else:
                        print(f"Failed to download video {index} after maximum retries. Moving to next video.")

    except exceptions.PytubeError as e:
        print(f"An error occurred while downloading the playlist. Details: {e}")
    except Exception as e:
        print(f"Unexpected error in playlist download: {e}")

# New function to select specific videos from a playlist
def select_videos(playlist):
    print("\nSelect the videos you want to download (enter numbers separated by commas):")
    for index, video in enumerate(playlist.videos, start=1):
       print(f"{index}. {video.title}")

    selections = input("Enter your selections: ")
    selected_indices = [int(i) - 1 for i in selections.split(',') if i.isdigit()]
    return [playlist.video_urls[i] for i in selected_indices if i < len(playlist.video_urls)]

# Main function to handle user input and start the download process
def main():
    try:
        log_dir = get_default_directory('log')
        download_dir = get_default_directory('download')
        url = None  # Initialize url to None
        download_mode = input("Enter 'S' for single download or 'B' for batch download: ").lower()
        download_choice = input("Would you like to download Video or Audio? Please enter 'V' for Video or 'A' for Audio: ").lower()
        if download_mode == 'b':
            batch_mode = input("Enter 'U' to input URLs or 'F' to read from a file: ").lower()
            if batch_mode == 'u':
                urls = input("Enter video URLs separated by commas: ").split(',')
            elif batch_mode == 'f':
                file_path = input("Enter the file path containing video URLs: ")
                with open(file_path, 'r') as file:
                    urls = file.read().splitlines()
            else:
                raise ValueError("Invalid batch mode selected")

            path = input("Enter the download directory: ")
            os.makedirs(path, exist_ok=True)
            batch_download(urls, path, download_choice, log_dir)
        else:
            url = input("Please enter the full YouTube URL (video or playlist): ")
            is_playlist = 'playlist' in url
            print(f"Default log file directory is '{log_dir}'.")

            # Handling downloads for playlists and individual videos or audio
            if is_playlist:
                playlist_choice = input("Do you want to download the entire playlist or select specific videos? Enter 'E' for entire or 'S' for select: ").lower()
                playlist_path = input("\nEnter the folder name for the playlist: ")
                path = os.path.join(download_dir, "/Playlists", playlist_path)
                os.makedirs(path, exist_ok=True)
                download_playlist(url, path, download_choice, log_dir, playlist_choice)  # Pass download_choice here
            else:
                yt = YouTube(url)
                if download_choice == 'v':
                    video_path = os.path.join(download_dir, "/Videos")
                    os.makedirs(video_path, exist_ok=True)
                    download_highest_quality_video(yt, video_path, log_dir)
                elif download_choice == 'a':
                    audio_path = os.path.join(download_dir, "/Music")
                    os.makedirs(audio_path, exist_ok=True)
                    download_audio(yt, audio_path, log_dir)
    except ValueError as e:
        print(f"Invalid input: {e}")
        log_download_details(url, "Failed", log_dir, str(e))
    except Exception as e:
        log_download_details(url, "Failed", log_dir, str(e))
        print(f"Unexpected error: {e}")
    except KeyboardInterrupt:
        if url:
            log_download_details(url, "Interrupted", log_dir, "User stopped the program")
        else:
            print("\nProgram stopped by the user before URL was provided. Exiting now...")

if __name__ == "__main__":
    main()
