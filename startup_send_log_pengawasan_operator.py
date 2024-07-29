import os
import time
import signal
import sys
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta, date  # Added 'date' here
import pytz
from pathlib import Path
import requests
import sqlite3
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('script.log'),
        logging.StreamHandler()
    ]
)

# Add initial logging
logging.info("Starting the script...")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_conda_path():
    try:
        conda_path = r'C:\ProgramData\anaconda3\Scripts\conda.exe'
        logging.info(f"Conda path found: {conda_path}")
        return conda_path
    except subprocess.CalledProcessError:
        logging.error("Conda not found in PATH.")
        return None

def activate_conda_env(env_name):
    conda_path = get_conda_path()
    if not conda_path:
        logging.error("Failed to find Conda executable.")
        return
    try:
        activate_cmd = f'"{conda_path}" activate {env_name}'
        subprocess.run(activate_cmd, shell=True, check=True)
        logging.info(f"The {env_name} environment is activated.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to activate environment {env_name}: {e}")

def open_directory(path):
    try:
        process = subprocess.Popen(['explorer', path])
        logging.info(f"Opened directory: {path}")
        return process
    except FileNotFoundError as e:
        logging.error(f"Failed to open directory {path}: {e}")
        return None

API_URL = "https://srs-ssms.com/op_monitoring/insert_log_pengawasan_operator.php"
DB_PATH = "operator_behaviour.db"
MACHINE_ID = 1
INTERVAL = timedelta(minutes=5)

def get_data_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = date.today().strftime("%Y-%m-%d")
    
    cursor.execute('''
        SELECT uptime FROM pengawasan_operator
        WHERE date = ? AND machine_id = ?
    ''', (today, MACHINE_ID))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def send_data_to_api(data):
    payload = {
        "machine_id": MACHINE_ID,
        "date": date.today().strftime("%Y-%m-%d"),
        "uptime": data
    }
    
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        print(f"Data sent successfully at {datetime.now()}")
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

base_dir = r'C:\Users\User\Documents\pengawasan_operator_ai'

if __name__ == "__main__":
    # Define the base directory
    open_dir = base_dir

    env_name = 'yolov8'
    activate_conda_env(env_name)

    # Open directory
    open_dir_process = open_directory(open_dir)

    next_run = datetime.now() + INTERVAL
    while True:
        data = get_data_from_db()
        if data:
            send_data_to_api(data)
        else:
            print("No data found for today")
        
        sleep_time = (next_run - datetime.now()).total_seconds()
        if sleep_time > 0:
            time.sleep(sleep_time)
        next_run += INTERVAL