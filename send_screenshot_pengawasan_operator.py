import os
import datetime
import pytz
import requests
import argparse
import hashlib

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Send a file to the API endpoint.")
parser.add_argument("--file", required=True, help="Path to the file to be sent")
args = parser.parse_args()

# Set the API endpoint URL
send_screenshot_url = "https://srs-ssms.com/op_monitoring/send_screenshot_pengawasan.php"

# Set the timezone to Asia/Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Get the file path from the command-line argument
file_path = args.file

# Send the file to the API endpoint
with open(file_path, "rb") as file:
    files = {"image": (os.path.basename(file_path), file, "image/jpeg")}
    send_screenshot_response = requests.post(send_screenshot_url, files=files)

# Check the response status code
if send_screenshot_response.status_code == 200:
    print(f"File {os.path.basename(file_path)} uploaded successfully.")
else:
    print(f"Error uploading file {os.path.basename(file_path)}: {send_screenshot_response.text}")
