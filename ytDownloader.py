from pytube import YouTube
from pytube import Playlist
import os 

try:
    # Ask the user to input the YouTube URL
    url = input("Enter the youtube URL download : ")
    # Ask the user to input if URL is playlist or not
    videotype = input("Is video you want download is playlist( y or n ): ")
    if videotype == "y":
        directory = input("Enter Playlist folder name : ")
        parent_dir = "D:\Videos\Playlist"

        path = os.path.join(parent_dir, directory) 
        try:
            os.mkdir(path)  
            print("Directory '% s' created" % directory) 
        except OSError as error: 
            print(error)
        yt = Playlist(url)

        print("Downloading:", yt.title)
        for video in yt.videos:
            video.streams.get_highest_resolution().download(path)
    else:
        yt = YouTube(url)

        print("Downloading:", yt.title)
        # Get the highest resolution stream
        yd = yt.streams.get_highest_resolution()
        # Download the video to the current directory
        yd.download('D:\Videos')
    
    print("Download complete.")
except Exception as e:
    print("An error occurred:", str(e))
