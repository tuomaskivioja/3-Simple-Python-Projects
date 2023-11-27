from download_utils import batch_download, download_playlist, download_audio, download_highest_quality_video, parse_arguments
from file_utils import get_default_directory
from logging_utils import log_download_details
from pytube import YouTube
import os, requests

CURRENT_VERSION = "1.0.0"

def check_for_updates():
    update_url = "http://example.com/latest_version.txt"  # URL where the latest version number is stored
    try:
        response = requests.get(update_url)
        latest_version = response.text.strip()
        if latest_version != CURRENT_VERSION:
            print(f"Update available: Version {latest_version} is available. You are using version {CURRENT_VERSION}.")
            # You can add more instructions here on how to update
    except requests.RequestException as e:
        print(f"Failed to check for updates: {e}")

# Main function to handle user input and start the download process
def main():
    try:
        check_for_updates()
        args = parse_arguments()

        log_dir = get_default_directory('log')
        download_dir = args.directory if args.directory else get_default_directory('download')

        if args.mode == 'batch':
            if args.urls:
                urls = args.urls
            elif args.file:
                with open(args.file, 'r') as file:
                    urls = file.read().splitlines()
            else:
                raise ValueError("URLs or a file path is required for batch download")
            os.makedirs(download_dir, exist_ok=True)
            batch_download(urls, download_dir, args.type, log_dir)
        elif args.mode == 'single':
            if not args.urls:
                raise ValueError("URL is required for single download")
            url = args.urls[0]
            if args.playlist:
                playlist_path = os.path.join(download_dir, "Playlists")
                os.makedirs(playlist_path, exist_ok=True)
                download_playlist(url, playlist_path, args.type, log_dir, args.playlist_choice)
            else:
                if args.type == 'video':
                    video_path = os.path.join(download_dir, "Videos")
                    os.makedirs(video_path, exist_ok=True)
                    yt = YouTube(url)
                    download_highest_quality_video(yt, video_path, log_dir)
                elif args.type == 'audio':
                    audio_path = os.path.join(download_dir, "Music")
                    os.makedirs(audio_path, exist_ok=True)
                    yt = YouTube(url)
                    download_audio(yt, audio_path, log_dir)
        else:
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
