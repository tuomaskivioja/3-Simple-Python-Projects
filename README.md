# YouTube Downloader Script

Welcome to our YouTube Downloader Script! This Python-based tool offers a versatile and efficient way to download videos and playlists from YouTube. Whether you're looking for the highest quality video, or just the audio track, our script has got you covered. Read on to discover its key features, installation process, and how you can configure it for your own use.

## Key Features

- **Versatile Download Options**: Download individual videos, complete playlists, or batch downloads. Choose between video and audio formats.
- **High-Quality Downloads**: Fetches the highest available quality for videos and audios.
- **Batch Downloading**: Supports downloading multiple videos at once, either by entering URLs or reading from a file.
- **Integrity Checks**: Ensures the integrity of the downloaded files using FFmpeg.
- **Logging System**: Maintains a detailed log of all download activities for troubleshooting and record-keeping.
- **User-Friendly Interface**: Simple and interactive prompts guide the user through the download process.
- **File Sanitization and Renaming**: Automatically handles invalid characters in filenames and provides options for renaming existing files.
- **Playlist Support**: Download entire playlists or select specific videos from a playlist.
- **Automatic Metadata Tagging**: Automatically tags downloaded audio files with relevant metadata.
- **Retry Mechanism**: In case of failures, the script retries downloading the file.

## Installation

1. **Clone the Repository**:

   ```
   git clone https://github.com/tejasholla/YouTube-Downloader.git
   ```

2. **Install Dependencies**:

   - Python 3.x or higher is required.
   - Install Pytube: `pip install pytube`.
   - Install tqdm: `pip install tqdm`.
   - Install tqdm: `pip install mutagen`.
   - Ensure FFmpeg is installed and added to your system's PATH.

## Configuration

- **FFmpeg Path**: Set the path to your FFmpeg installation in the script.
- **Download Path**: Customize the default paths for saving videos and audios.
- **Log Directory**: Choose a directory for saving log files.

## Usage

- Run the script using `python ytdownloader.py`.
- Follow the interactive prompts to choose your download options and enter URLs.

### Using Commandline Argument

- **Downloading a Single Video as Audio**:

  ```css
  python ytDownloader.py -m single -t audio -u https://www.youtube.com/watch?v=example
  ```

- **Downloading a Batch of Videos as Video**:

  ```css
  python ytDownloader.py -m batch -t video -u https://www.youtube.com/watch?v=example1 https://www.youtube.com/watch?v=example2
  ```

- **Downloading from a File Containing URLs**:

  ```css
  python ytDownloader.py -m batch -t video -f path_to_file.txt
  ```

- **Specifying a Download Directory**:

  ```css
  python ytDownloader.py -m single -t audio -u https://www.youtube.com/watch?v=example -d C:\Users\YourName\Downloads
  ```

- **Downloading an Entire Playlist as Audio**:

  ```css
  python ytDownloader.py -m single -t audio -p -u https://www.youtube.com/playlis
  ```


## Tips and Tricks
- **Handling Large Playlists**: For large playlists, consider downloading in batches to manage bandwidth and storage effectively.
- **Custom Metadata**: Customize the fetch_metadata function to fetch more detailed metadata from external APIs.
- **Error Handling**: Check the log files for detailed error messages in case of download failures.

## Contributing

If you find this script useful, please consider starring the repository and contributing with your ideas and improvements. Your feedback and contributions are highly appreciated!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

A big thank you to everyone who contributes to this project, and to all the users and developers who have made Python and its libraries such robust and versatile tools for the community.

***

Happy Downloading! 🎉📥

***

*Note: This script is for educational purposes only. Please adhere to YouTube's terms of service when using this tool.*
