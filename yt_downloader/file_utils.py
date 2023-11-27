import os, sys
import subprocess

# Function to get FFmpeg path based on the operating system
def get_ffmpeg_path():
    ffmpeg_path = 'ffmpeg'
    if sys.platform == 'win32':
        ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg.exe'
    elif shutil.which(ffmpeg_path) is None:
        raise EnvironmentError("FFmpeg not found. Ensure it's installed and added to your PATH.")
    return ffmpeg_path

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

# Function to merge video and audio files using FFmpeg
def merge_files(video_path, audio_path, output_path):
    ffmpeg_path = get_ffmpeg_path()
    subprocess.run([ffmpeg_path, '-i', video_path, '-i', audio_path, '-c', 'copy', output_path])

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