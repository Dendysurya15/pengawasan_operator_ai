import os
import requests
import argparse

# Set up the command-line argument parser
parser = argparse.ArgumentParser(description="Send a file to the API endpoint.")
parser.add_argument("--file", required=True, help="Path to the file to be sent")
parser.add_argument("--date_now", required=True, help="Current date and time")
parser.add_argument("--machine_id", required=True, help="Machine ID")
args = parser.parse_args()

# Set the API endpoints
send_screenshot_url = "https://srs-ssms.com/op_monitoring/send_screenshot_pengawasan.php"
post_unattended_data = "https://srs-ssms.com/op_monitoring/post_unattended.php"  # New endpoint for date_now and machine_id

# Get the file path, date, and machine ID from the command-line arguments
file_path = args.file
date_now = args.date_now
machine_id = args.machine_id

# Send the file to the API endpoint
with open(file_path, "rb") as file:
    files = {"image": (os.path.basename(file_path), file, "image/jpeg")}
    send_screenshot_response = requests.post(send_screenshot_url, files=files)

# First if-else block: Check the response status code for the file upload
if send_screenshot_response.status_code == 200:
    print(f"File {os.path.basename(file_path)} uploaded successfully.")
else:
    print(f"Error uploading file {os.path.basename(file_path)}: {send_screenshot_response.status_code} - {send_screenshot_response.text}")
# Now send the additional data (date_now and machine_id) to the new API endpoint
data = {
    "date_now": date_now,
    "machine_id": machine_id
}
response_unattended_post = requests.post(post_unattended_data, data=data)

# Second if-else block: Check the response for the additional data
if response_unattended_post.status_code == 200:
    print("Response from unattended post:", response_unattended_post.text)
else:
    print(f"Error sending additional data: {response_unattended_post.status_code} - {response_unattended_post.text}")
