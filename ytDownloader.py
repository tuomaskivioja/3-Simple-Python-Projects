import os, requests
from requests.exceptions import ConnectionError
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
import threading

CURRENT_VERSION = "1.0.6"

analytics_file = "download_analytics.json"
Preferences_file = "user_preferences.json"

# Constants for retry mechanism
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def load_preferences():
    try:
        with open(Preferences_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"download_directory": get_default_directory('download'), "log_directory": get_default_directory('log')}

def save_preferences(preferences):
    with open(Preferences_file, "w") as file:
        json.dump(preferences, file, indent=4)

def update_preferences(preferences):
    new_download_dir = input("Enter new download directory or press Enter to keep current: ")
    new_log_dir = input("Enter new log directory or press Enter to keep current: ")
    
    if new_download_dir:
        preferences['download_directory'] = new_download_dir
    if new_log_dir:
        preferences['log_directory'] = new_log_dir

    save_preferences(preferences)
    print("Preferences updated successfully.") 

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
    print(f"Audio Downloads: {data['audio_downloads']}\n")

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

def threaded_download(yt, path, download_choice, log_dir, max_retries=MAX_RETRIES):
    """
    Function to handle download in a separate thread with retry logic.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if download_choice == 'Video':
                download_highest_quality_video(yt, path, log_dir)
            elif download_choice == 'Audio':
                download_audio(yt, path, log_dir)
            break  # Break out of the loop if download is successful
        except exceptions.PytubeError as e:
            print(f"Pytube error during download: {e}")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
        finally:
            attempt += 1

        if attempt < max_retries:
            print(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            print("Maximum retries reached. Moving to next URL or video.")

def batch_download(urls, path, download_choice, log_dir):
    threads = []
    for url in urls:
        try:
            yt = YouTube(url)
            t = threading.Thread(target=threaded_download, args=(yt, path, download_choice, log_dir, MAX_RETRIES))
            threads.append(t)
            t.start()
        except Exception as e:
            print(f"Error setting up batch download: {e}")

    for thread in threads:
        thread.join()

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
        video_urls = pl.video_urls if playlist_choice == 'Entire' else select_videos(pl)
        threads = []
        for video_url in video_urls:
            try:
                yt = YouTube(video_url)
                t = threading.Thread(target=threaded_download, args=(yt, path, download_choice, log_dir, MAX_RETRIES))
                threads.append(t)
                t.start()
            except Exception as e:
                print(f"Error setting up playlist download: {e}")

        for thread in threads:
            thread.join()

    except Exception as e:
        print(f"Unexpected error in playlist download: {e}")

def create_custom_playlist():
    custom_playlist = []
    print("\nCustom Playlist Creation")
    print("Enter the URLs of the playlists or channels from which you want to select videos.")

    while True:
        add_more = inquirer.prompt([
            inquirer.Confirm('add_more', message="Would you like to add a Playlist/Channel URL?", default=True),
        ])

        if add_more['add_more']:
            url = input("Enter Playlist/Channel URL: ")

        if 'playlist' in url:
            pl = Playlist(url)
            playlist_choice = inquirer.prompt([
                inquirer.List('choice',
                              message="Do you want to download the entire playlist or select specific videos?",
                              choices=['Entire Playlist', 'Select Videos'],
                              ),
            ])

            if playlist_choice['choice'] == 'Entire Playlist':
                custom_playlist.extend(pl.video_urls)
            elif playlist_choice['choice'] == 'Select Videos':
                selected_videos = select_videos(pl)
                custom_playlist.extend(selected_videos)
        else:
            break

    return custom_playlist

def select_videos(playlist):
    """
    Interactive prompt for selecting specific videos from a playlist.
    """
    video_choices = [f"{index + 1}. {video.title}" for index, video in enumerate(playlist.videos)]
    questions = [inquirer.Checkbox('selected_videos',
                                   message="Select the videos you want to download (use space to select, enter to confirm):",
                                   choices=video_choices)]
    answers = inquirer.prompt(questions)
    selected_indices = [int(choice.split('.')[0]) - 1 for choice in answers['selected_videos']]
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

def download_and_replace_script(latest_script_url):
    try:
        response = requests.get(latest_script_url)
        if response.status_code == 200:
            # Assuming your script's filename is 'script.py'
            with open("ytDownloader.py", 'wb') as file:
                file.write(response.content)
            print("Script updated successfully. Please restart the script.")
            exit()
        else:
            print("Failed to download the update.")
    except Exception as e:
        print(f"Error during update: {e}")

def check_for_updates(retry_count=1, retry_delay=2):
    update_url = "https://raw.githubusercontent.com/tejasholla/YouTube-Downloader/master/latest_version.txt"  # URL where the latest version number is stored
    script_url = "https://raw.githubusercontent.com/tejasholla/YouTube-Downloader/master/ytDownloader.py"  # URL to your script file
    
    attempts = 0
    while attempts < retry_count:
        try:
            response = requests.get(update_url)
            if response.status_code == 200:
                latest_version = response.text.strip()
                if latest_version != CURRENT_VERSION:
                    print(f"Update available: Version {latest_version} is available. You are using version {CURRENT_VERSION}.")
                    # Ask the user if they wish to update
                    questions = [
                    inquirer.List('update',
                                message="Would you like to update to the latest version?",
                                choices=['Yes', 'No'],
                                ),
                ]
                answer = inquirer.prompt(questions)
                if answer['update'] == 'Yes':
                    download_and_replace_script(script_url)
                break  # Break the loop if successful
            else:
                print("Failed to download the update.")
                break
        except ConnectionError:
            if attempts < retry_count - 1:
                time.sleep(retry_delay)
        except Exception as e:
            print(f"Unexpected error while checking for updates: {e}")
            break
        finally:
            attempts += 1

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
        url = None
        #args = parse_arguments()
        preferences = load_preferences()
        #log_dir = get_default_directory('log')
        log_dir = preferences['log_directory']
        #download_dir = args.directory if args.directory else get_default_directory('download')
        download_dir = preferences['download_directory']

        print("\nYouTube Downloader [" + CURRENT_VERSION + "]")

        while True:  # Continuous loop until exit is chosen
            questions = [
                inquirer.List('choice',
                              message="Please enter your choice",
                              choices=['Download Video/Audio', 'View Download Analytics', 'Settings', 'Exit'],
                              ),
            ]
            answers = inquirer.prompt(questions)

            if answers['choice'] == 'Download Video/Audio':
                download_choice = interactive_prompt("What do you want to download?", ["Video", "Audio"])
                mode_choice = interactive_prompt("Choose download mode", ["Single", "Batch", "Custom Playlist"])

                if mode_choice == 'Batch':
                    batch_mode = interactive_prompt("Select batch mode", ["Enter URLs", "Use File"])
                    if batch_mode == "Enter URLs":
                        urls = input("Enter video URLs separated by commas: ").split(',')
                    elif batch_mode == "Use File":
                        file_path = input("Enter the file path containing video URLs: ")
                        with open(file_path, 'r') as file:
                            urls = file.read().splitlines()
                    if download_choice == 'Video':
                        video_path = os.path.join(download_dir, "Videos")
                        os.makedirs(video_path, exist_ok=True)
                        batch_path = video_path
                    elif download_choice == 'Audio':
                        audio_path = os.path.join(download_dir, "Music")
                        os.makedirs(audio_path, exist_ok=True)
                        batch_path = audio_path
                    batch_download(urls, batch_path, download_choice, log_dir)
                elif mode_choice == 'Custom Playlist':
                    playlist_name = input("Enter a name for your custom playlist: ")
                    custom_playlist_urls = create_custom_playlist()
                    custom_playlist_path = os.path.join(download_dir, "Playlists", playlist_name)
                    os.makedirs(custom_playlist_path, exist_ok=True)
                    if download_choice == 'Video':
                        batch_download(custom_playlist_urls, custom_playlist_path, "Video", log_dir)
                    elif download_choice == 'Audio':
                        batch_download(custom_playlist_urls, custom_playlist_path, "Audio", log_dir)
                else:
                    url = input("Please enter the full YouTube URL (video or playlist): ")
                    if 'playlist' in url:
                        playlist_choice = interactive_prompt("Download entire playlist or select specific videos?", ["Entire", "Select"])
                        playlist_path = input("\nEnter the folder name for the playlist: ")
                        path_playlist = os.path.join(download_dir, "Playlists", playlist_path)
                        os.makedirs(path_playlist, exist_ok=True)
                        download_playlist(url, path_playlist, download_choice, log_dir, playlist_choice)
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

            elif answers['choice'] == 'Settings':
                settings_choice = interactive_prompt("Select a setting to update", ["Update Preferences", "Feedback and Support", "Back to Main Menu"])
                if settings_choice == 'Update Preferences':
                    update_preferences(preferences)
                elif settings_choice == 'Feedback and Support':
                    feedback_and_support()

            elif answers['choice'] == 'Exit':
                save_preferences(preferences)
                print("Exiting YouTube Downloader CLI.")
                break  # Exit the loop and the program

            else:
                print("Invalid choice. Please enter a valid option.")

    except KeyboardInterrupt:
        if url:
            log_download_details(url, "Interrupted", log_dir, "User stopped the program")
        else:
            print("\nProgram stopped by the user before URL was provided. Exiting now...")
    except ValueError as e:
        print(f"Invalid input: {e}")
        log_download_details(url, "Failed", log_dir, str(e))
    except Exception as e:
        log_download_details(url, "Failed", log_dir, str(e))
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
