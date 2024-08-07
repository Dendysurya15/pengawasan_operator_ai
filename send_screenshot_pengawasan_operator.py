import os
import datetime
import pytz
import requests
import argparse
import hashlib
import time
from pathlib import Path

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Monitor directory and send files to API endpoint.")
parser.add_argument("--script_dir", default=os.getcwd(), help="Directory to monitor (default: current working directory)")
args = parser.parse_args()

# Set the directory to monitor
script_dir = args.script_dir

# Set the API endpoint URLs
send_screenshot_url = "https://srs-ssms.com/op_monitoring/send_screenshot_pengawasan.php"
check_file_url = "https://srs-ssms.com/op_monitoring/check_screenshot_exist.php"

# Set the time interval (in minutes)
time_interval = datetime.timedelta(seconds=10, minutes=0)

# Set the timezone to Asia/Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

# List of allowed image extensions
image_extensions = ['.png', '.jpg', '.jpeg']

while True:
    # Get the current date in Asia/Jakarta timezone
    current_date = datetime.datetime.now(jakarta_tz).strftime("%Y_%m_%d")

    # Create the folder for the current date
    folder_path = os.path.join(script_dir, "screenshots", current_date)
    os.makedirs(folder_path, exist_ok=True)

    # Loop through all files in the folder for the current date
    for file_path in Path(folder_path).rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            # Calculate the file hash
            file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()

            # Check if the file exists on the server
            check_file_params = {"file_hash": file_hash}
            check_file_response = requests.get(check_file_url, params=check_file_params)

            if check_file_response.status_code == 200 and check_file_response.text == "File not found":
                # Send the file to the API endpoint
                with open(file_path, "rb") as file:
                    files = {"image": (file_path.name, file, "image/jpeg")}
                    send_screenshot_response = requests.post(send_screenshot_url, files=files)

                # Check the response status code
                if send_screenshot_response.status_code == 200:
                    print(f"File {file_path.name} uploaded successfully.")
                else:
                    print(f"Error uploading file {file_path.name}: {send_screenshot_response.text}")
            else:
                print(f"File {file_path.name} already exists on the server.")

    # Calculate the next time to run the loop
    next_run = datetime.datetime.now(jakarta_tz) + time_interval


    print(datetime.datetime.now(jakarta_tz))
    # Wait until the next run time
    time_to_wait = (next_run - datetime.datetime.now(jakarta_tz)).total_seconds()
    time.sleep(time_to_wait)
