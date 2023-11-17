from pytube import YouTube
from pytube import Playlist
from tqdm import tqdm
import os 

try:
    # Ask the user to input the YouTube URL
    url = input("Enter the youtube URL to download : ")
    # Ask the user to input if URL is playlist or not
    videotype = input("Is it a playlist( y or n ): ")
    audioorvideo = input("Do you want only audio( y or n ): ")
    if videotype == "y":
        directory = input("Enter Playlist folder name : ")
        parent_dir = "D:/Videos/Playlist"

        path = os.path.join(parent_dir, directory) 
        try:
            os.mkdir(path)  
            print("Directory '% s' created" % directory) 
        except OSError as error: 
            print(error)
        yt = Playlist(url)

        print("Downloading:", yt.title)
        if audioorvideo == "y":
            for video in tqdm(yt.videos):
                video.streams.gfilter(only_audio=True).first().download(path) # Downloader for audio
        else:
            for video in tqdm(yt.videos):
                video.streams.get_highest_resolution().download(path) # Downloader for video
    else:
        yt = YouTube(url)

        print("Downloading:", yt.title)
        if audioorvideo == "y":
            # Get the highest resolution stream
            yd = yt.streams.filter(only_audio=True).first().download('D:/Music') # Downloader for audio
        else:   
            # Get the highest resolution stream
            yd = yt.streams.get_highest_resolution().download('D:/Videos') # Downloader for video

    print("Download complete.")
except Exception as e:
    print("An error occurred:", str(e))
