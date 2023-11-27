from download_utils import batch_download, download_playlist, download_audio, download_highest_quality_video
from file_utils import get_default_directory
from logging_utils import log_download_details
from pytube import YouTube
import os

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
