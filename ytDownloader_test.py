import os, requests
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
import argparse
import inquirer
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CURRENT_VERSION = "1.0.2"

analytics_file = "download_analytics.json"

# Constants for retry mechanism
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def update_analytics(download_type, file_size):
    if not os.path.exists(analytics_file):
        data = {"total_downloads": 0, "total_data_downloaded": 0, "video_downloads": 0, "audio_downloads": 0}
    else:
        with open(analytics_file, 'r') as f:
            data = json.load(f)

    data["total_downloads"] += 1
    data["total_data_downloaded"] += file_size
    if download_type == "video":
        data["video_downloads"] += 1
    elif download_type == "audio":
        data["audio_downloads"] += 1

    with open(analytics_file, 'w') as f:
        json.dump(data, f, indent=4)

def display_analytics():
    if not os.path.exists(analytics_file):
        print("No download data available.")
        return

    with open(analytics_file, 'r') as f:
        data = json.load(f)

    print("\nDownload Analytics:")
    print(f"Total Downloads: {data['total_downloads']}")
    print(f"Total Data Downloaded: {data['total_data_downloaded']} MB")
    print(f"Video Downloads: {data['video_downloads']}")
    print(f"Audio Downloads: {data['audio_downloads']}")

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
                if download_choice == 'Video':
                    download_highest_quality_video(yt, path, log_dir)
                elif download_choice == 'Audio':
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

            try:
                # Assuming the final file path is stored in 'final_path'
                file_size_MB = os.path.getsize(final_path) / (1024 * 1024)  # Convert bytes to MB
                update_analytics("video", file_size_MB)
            except Exception as e:
                print(f"Error updating analytics for video: {e}")

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

def interactive_prompt(question, choices):
    questions = [inquirer.List('choice', message=question, choices=choices)]
    return inquirer.prompt(questions)['choice']

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
                user_input = interactive_prompt(f"{final_filename} already exists. Would you like to skip downloading this file?", ["Yes", "No"])                
                if user_input == 'Yes':
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

            try:
                # Assuming the final file path is stored in 'file_path'
                file_size_MB = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to MB
                update_analytics("audio", file_size_MB)
            except Exception as e:
                print(f"Error updating analytics for audio: {e}")

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

        video_urls = pl.video_urls if playlist_choice == 'Entire' else select_videos(pl)

        if playlist_choice == 'Select':
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

def parse_arguments():
    parser = argparse.ArgumentParser(description="YouTube Video and Audio Downloader")
    
    parser.add_argument("-m", "--mode", choices=['single', 'batch'], help="Download mode: single or batch")
    parser.add_argument("-t", "--type", choices=['video', 'audio'], help="Download type: video or audio")
    parser.add_argument("-u", "--urls", nargs='+', help="List of URLs to download for batch mode")
    parser.add_argument("-f", "--file", type=str, help="File path containing URLs for batch mode")
    parser.add_argument("-d", "--directory", type=str, help="Download directory")
    parser.add_argument("-p", "--playlist", action="store_true", help="Indicates the URL is a playlist")
    parser.add_argument("-plc", "--playlist_choice", choices=['e', 's'], help="Download entire playlist or select specific videos (e/s)")
    parser.add_argument("-r", "--retries", type=int, default=3, help="Set the maximum number of retries for downloads")

    return parser.parse_args()

def check_for_updates():
    update_url = "https://raw.githubusercontent.com/tejasholla/YouTube-Downloader/master/latest_version.txt"  # URL where the latest version number is stored
    try:
        response = requests.get(update_url)
        latest_version = response.text.strip()
        if latest_version != CURRENT_VERSION:
            print(f"Update available: Version {latest_version} is available. You are using version {CURRENT_VERSION}.")
            # You can add more instructions here on how to update
    except requests.RequestException as e:
        print(f"Failed to check for updates: {e}")

def send_feedback_via_email(user_input):
    # Email Configuration
    sender_email = "your_email@gmail.com"  # Replace with your email
    sender_password = "your_password"  # Replace with your email password
    receiver_email = "support@example.com"  # Replace with the support email

    # Set up the MIME
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "New Feedback/Support Request"

    # Email body
    body = f"User Feedback/Support Request:\n\n{user_input}"
    message.attach(MIMEText(body, 'plain'))

    # SMTP Server and send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("Feedback/Support request sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

def feedback_and_support():
    print("\nFeedback and Support System")
    print("Please enter your feedback or describe the issue you're facing. Type 'exit' to return to the main menu.")

    while True:
        user_input = input("\nEnter your feedback/support request: ")

        if user_input.lower() == 'exit':
            break

        send_feedback_via_email(user_input)

# Main function to handle user input and start the download process
def main():
    try:
        check_for_updates()
        log_dir = get_default_directory('log')
        download_dir = get_default_directory('download')

        while True:  # Continuous loop until exit is chosen
            print("\nWelcome to YouTube Downloader CLI!")

            questions = [
                inquirer.List('choice',
                              message="Please enter your choice",
                              choices=['Download Video/Audio', 'View Download Analytics', 'Feedback and Support', 'Exit'],
                              ),
            ]
            answers = inquirer.prompt(questions)

            if answers['choice'] == 'Download Video/Audio':
                download_choice = interactive_prompt("What do you want to download?", ["Video", "Audio"])
                mode_choice = interactive_prompt("Choose download mode", ["Single", "Batch"])

                if mode_choice == 'Batch':
                    batch_mode = interactive_prompt("Select batch mode", ["Enter URLs", "Use File"])
                    if batch_mode == "Enter URLs":
                        urls = input("Enter video URLs separated by commas: ").split(',')
                    elif batch_mode == "Use File":
                        file_path = input("Enter the file path containing video URLs: ")
                        with open(file_path, 'r') as file:
                            urls = file.read().splitlines()
                    batch_download(urls, download_dir, download_choice, log_dir)
                else:
                    url = input("Please enter the full YouTube URL (video or playlist): ")
                    if 'playlist' in url:
                        playlist_choice = interactive_prompt("Download entire playlist or select specific videos?", ["Entire", "Select"])
                        playlist_path = os.path.join(download_dir, "Playlists")
                        os.makedirs(playlist_path, exist_ok=True)
                        download_playlist(url, playlist_path, download_choice, log_dir, playlist_choice)
                    else:
                        if download_choice == 'Video':
                            video_path = os.path.join(download_dir, "Videos")
                            os.makedirs(video_path, exist_ok=True)
                            yt = YouTube(url)
                            download_highest_quality_video(yt, video_path, log_dir)
                        elif download_choice == 'Audio':
                            audio_path = os.path.join(download_dir, "Music")
                            os.makedirs(audio_path, exist_ok=True)
                            yt = YouTube(url)
                            download_audio(yt, audio_path, log_dir)

            elif answers['choice'] == 'View Download Analytics':
                display_analytics()

            elif answers['choice'] == 'Feedback and Support':
                feedback_and_support()

            elif answers['choice'] == 'Exit':
                print("Exiting YouTube Downloader CLI.")
                break  # Exit the loop and the program

            else:
                print("Invalid choice. Please enter a valid option.")

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
