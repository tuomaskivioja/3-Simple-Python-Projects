# YouTube Video and Audio Downloader

This Python script provides a convenient way to download videos and audio tracks from YouTube. It supports both single and batch downloads, with options for downloading either the full video or just the audio track. The script utilizes the `pytube` library and includes features such as progress tracking, file integrity checks, and filename sanitization.

## Features

- **Single and Batch Downloads:** Download individual videos or entire playlists.
- **Video and Audio Support:** Choose to download either video files or audio tracks.
- **Progress Bar:** Visual progress indication for downloads.
- **File Integrity Check:** Utilizes FFmpeg to check the integrity of downloaded files.
- **Filename Sanitization:** Automatically removes invalid characters from filenames.
- **Download Logs:** Maintains logs of all downloads, including any errors encountered.

## Prerequisites

Before running the script, ensure you have the following installed:
- Python 3.x
- FFmpeg (for file integrity checks and audio processing)

## Installation
### Clone the repository:
   ```bash
   git clone https://github.com/tejasholla/3-Simple-Python-Projects.git
   ```
## Install required Python packages:
   ```bash
   pip install pytube tqdm
   ```

## Usage
### Run the script from the command line:
   ```bash
   python youtube_downloader.py
   ```

_Follow the on-screen prompts to choose between single or batch downloads, video or audio, and other settings._

## Configuration
- Edit the script to set default download paths or FFmpeg executable path as needed.
- Customize logging preferences within the script.

## Contributing
**Contributions, issues, and feature requests are welcome. Feel free to check issues page if you want to contribute.**