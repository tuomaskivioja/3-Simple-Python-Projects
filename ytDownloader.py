from pytube import YouTube
from pytube import Playlist
from tqdm import tqdm
import pywhatkit as kit
from youtubesearchpython import VideosSearch
from tkinter import *
import os 

try:
    checkifurl = input("Do you have url ( y or n ) : ")
    if checkifurl == "y":
        # Ask the user to input the YouTube URL
        url = input("Enter the youtube URL to download : ")
    else:
        # Ask the user to input the YouTube video
        ytsearchres = input("What do you want to search : ")
        kit.playonyt(ytsearchres)
        #search = VideosSearch(ytsearchres,limit = 5)
        #print(search.result()['result'])
        # Ask the user to input the YouTube URL
        url = input("Enter the youtube URL to download : ")    

    # Ask the user to input if URL is playlist or not
    #videotype = input("Is it a playlist( y or n ): ")

    audioorvideo = input("Do you want only audio( y or n ): ")
    #if videotype == "y":
    if "playlist?list" in url:
        directory = input("Enter Playlist folder name : ")
        parent_dir = "D:/Videos/Playlist"

        path = os.path.join(parent_dir, directory) 
        try:
            os.mkdir(path)  
            print("Playlist folder '% s' created" % directory) 
        except OSError as error: 
            print(error)
        yt = Playlist(url)

        print("Downloading:", yt.title)
        if audioorvideo == "y":
            for video in tqdm(yt.videos):
                video.streams.filter(only_audio=True).first().download(path) # Downloader for audio
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
