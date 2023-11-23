import os
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Logging function to record download details
def log_download_details(url, status, log_dir, error_msg=None):
    """
    Log the details of a download attempt, including status and any error messages.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] URL: {url}, Status: {status}"

    if error_msg:
        log_message += f", Error: {error_msg}"
    
    try:
        # Create directory if it does not exist
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "download_history.log"), "a") as log_file:
            log_file.write(log_message + "\n")
    except OSError as e:
        print(f"Error creating log directory: {e}")
        return  # Exit the function if directory creation fails
    except Exception as e:
        print(f"Error logging details: {e}")