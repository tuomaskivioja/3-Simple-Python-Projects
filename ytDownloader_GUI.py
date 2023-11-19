import tkinter as tk
from tkinter import simpledialog, messagebox
from pytube import YouTube, Playlist
import os
import threading

# Predefined paths
video_path = "D:/Videos"
playlist_path = "D:/Videos/Playlists"
audio_path = "D:/Music"

def progress_function(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    progress_var.set(f"Downloading: {percentage_of_completion:.2f}%")
    progress_label.update()

def download_video(yt, path):
    yt.register_on_progress_callback(progress_function)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    stream.download(output_path=path)
    progress_var.set(f"Downloaded {yt.title} to {path}")
    progress_label.update()

def download_audio(yt, path):
    yt.register_on_progress_callback(progress_function)
    stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    stream.download(output_path=path, filename=f"{yt.title}.mp3")
    progress_var.set(f"Downloaded audio of {yt.title} to {path}")
    progress_label.update()

def get_playlist_folder_name():
    return simpledialog.askstring("Playlist Folder", "Enter a folder name for the playlist:")

def start_download(playlist_folder_name=None):
    url = url_entry.get()
    choice = var.get()
    is_playlist = 'playlist' in url

    if is_playlist:
        if not playlist_folder_name:
            messagebox.showerror("Error", "No folder name entered for the playlist")
            return
        full_playlist_path = os.path.join(playlist_path, playlist_folder_name)
        os.makedirs(full_playlist_path, exist_ok=True)

        pl = Playlist(url)
        total_videos = len(pl.video_urls)
        progress_var.set(f"Total videos in the playlist: {total_videos}")
        progress_label.update()

        downloaded_videos = 0
        for video_url in pl.video_urls:
            yt = YouTube(video_url)
            download_video(yt, full_playlist_path) if choice == 'V' else download_audio(yt, full_playlist_path)
            downloaded_videos += 1
            progress_var.set(f"Downloaded {downloaded_videos}/{total_videos} videos from playlist")
            progress_label.update()
    else:
        if choice == 'V':
            os.makedirs(video_path, exist_ok=True)
            yt = YouTube(url)
            download_video(yt, video_path)
        elif choice == 'A':
            os.makedirs(audio_path, exist_ok=True)
            yt = YouTube(url)
            download_audio(yt, audio_path)

def download_thread():
    playlist_folder_name = None
    if 'playlist' in url_entry.get():
        playlist_folder_name = get_playlist_folder_name()
        if not playlist_folder_name:
            return  # Exit if no folder name is provided
    threading.Thread(target=lambda: start_download(playlist_folder_name)).start()

# Tkinter GUI Setup
root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("600x300")  # Set the size of the window
root.configure(bg='black')  # Set the background color to black

# Use grid layout
label = tk.Label(root, text="Enter YouTube URL:", bg='black', fg='white')
label.grid(row=2, column=0, columnspan=2, pady=10)

url_entry = tk.Entry(root, width=70)
url_entry.grid(row=3, column=0, columnspan=2, padx=14, pady=7)

var = tk.StringVar(value='V')
video_button = tk.Radiobutton(root, text="Download Video", variable=var, value='V', bg='black', fg='orange')
audio_button = tk.Radiobutton(root, text="Download Audio", variable=var, value='A', bg='black', fg='orange')
video_button.grid(row=4, column=0, pady=5)
audio_button.grid(row=4, column=1, pady=5)

progress_var = tk.StringVar()
progress_label = tk.Label(root, textvariable=progress_var, bg='black', fg='white')
progress_label.grid(row=5, column=0, columnspan=2, pady=10)

download_button = tk.Button(root, text="Download", command=download_thread)
download_button.grid(row=6, column=0, columnspan=2, pady=10)

# Adjust the columns to center the elements
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

root.mainloop()