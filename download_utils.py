from pytube import YouTube, Playlist, exceptions
import subprocess
from tqdm import tqdm
from logging_utils import log_download_details
from progress_utils import download_with_progress
from file_utils import sanitize_filename, correct_file_extension, check_file_integrity, merge_files
import os

def batch_download(urls, path, download_choice, log_dir):
    for url in urls:
        try:
            yt = YouTube(url)
            if download_choice == 'v':
                download_highest_quality_video(yt, path, log_dir)
            elif download_choice == 'a':
                download_audio(yt, path, log_dir)
        except exceptions.PytubeError as e:
            log_download_details(url, "Failed", log_dir, str(e))
            print(f"Pytube error during batch download: {e}")
        except Exception as e:
            log_download_details(url, "Failed", log_dir, str(e))
            print(f"Unexpected error during batch download: {e}")

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
        # Log failed download
        log_download_details(yt.watch_url, "Failed", log_dir, str(e))
        print(f"Unexpected error: {e}")

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
def download_playlist(url, path, download_choice, log_dir):
    try:
        pl = Playlist(url)
        print(f"\nPlaylist details: ")
        print(f"Playlist name: {pl.title}")
        print(f"Total videos in the playlist: {len(pl.video_urls)}")

        # Loop through each video in the playlist and download based on user choice
        for index, video_url in enumerate(pl.video_urls, start=1):
            try:
                yt = YouTube(video_url)
                print(f"\nDownloading {('audio' if download_choice == 'a' else 'video')} {index} of {len(pl.video_urls)}: {yt.title}")
                if download_choice == 'v':
                    download_highest_quality_video(yt, path, log_dir)
                elif download_choice == 'a':
                    download_audio(yt, path, log_dir)
            except Exception as e:
                log_download_details(video_url, "Failed", log_dir, str(e))
                print(f"Error downloading video {index} in playlist: {e}")            
    except exceptions.PytubeError as e:
        print(f"An error occurred while downloading the playlist. Please check your network connection and try again. Details: {e}")
    except Exception as e:
        print(f"Unexpected error in playlist download: {e}")