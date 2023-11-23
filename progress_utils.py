from tqdm import tqdm
import time
import datetime
import logging, os

# Helper function to download with a progress bar
def download_with_progress(stream, file_path, yt):
    """
    Download a YouTube stream with an interactive progress bar showing detailed information.
    """
    logging.info(f"Starting download: {file_path}")

    tqdm_instance = tqdm(total=stream.filesize, unit='B', unit_scale=True, 
                         desc=f'Downloading {os.path.basename(file_path)}', 
                         ascii=True, miniters=1)

    last_time = time.time()
    last_bytes = 0

    def progress_function(stream, chunk, bytes_remaining):
        nonlocal last_time, last_bytes
        current_time = time.time()
        elapsed_time = current_time - last_time

        downloaded = stream.filesize - bytes_remaining
        tqdm_instance.update(downloaded - last_bytes)

        if elapsed_time > 0:
            # Calculate speed in KB/s
            speed = ((downloaded - last_bytes) / elapsed_time) / 1024
            eta = datetime.timedelta(seconds=int(bytes_remaining / (speed * 1024))) if speed > 0 else 'Unknown'
            eta_formatted = str(eta).split('.')[0] if isinstance(eta, datetime.timedelta) else eta
            tqdm_instance.set_postfix_str(f"Speed: {speed:.2f} KB/s, ETA: {eta_formatted}")

        last_time = current_time
        last_bytes = downloaded

    yt.register_on_progress_callback(progress_function)
    try:
        stream.download(filename=file_path)
        tqdm_instance.close()
        logging.info(f"Download completed: {file_path}")
    except Exception as e:
        logging.error(f"Error during download: {e}")
        tqdm_instance.close()