import requests
import sqlite3
import time
from datetime import date, datetime, timedelta
import asyncio
import aiohttp
import argparse
import subprocess
import sys
import os

API_URL = "https://srs-ssms.com/op_monitoring/insert_log_pengawasan_operator.php"
DB_PATH = "operator_behaviour.db"
INTERVAL = timedelta(minutes=5)

async def send_data_to_api(machine_id, data):
    async with aiohttp.ClientSession() as session:
        payload = {
            "machine_id": machine_id,
            "date": date.today().strftime("%Y-%m-%d"),
            "uptime": data
        }
        
        async with session.post(API_URL, json=payload) as response:
            if response.status == 200:
                print(f"Data sent successfully for machine {machine_id} at {datetime.now()}")
            else:
                print(f"Failed to send data for machine {machine_id}. Status code: {response.status}")

def get_data_from_db(machine_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = date.today().strftime("%Y-%m-%d")
    
    cursor.execute('''
        SELECT uptime FROM pengawasan_operator
        WHERE date = ? AND machine_id = ?
    ''', (today, machine_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def setup_database(script_dir):
    try:
        subprocess.run([sys.executable, os.path.join(script_dir, "setup_database.py")], check=True)
        print("Database setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running setup_database.py: {e}")
        sys.exit(1)

async def main(script_dir):
    setup_database(script_dir)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM machine WHERE status != 0")
    machine_ids = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    while True:
        tasks = []
        for machine_id in machine_ids:
            data = get_data_from_db(machine_id)
            if data:
                tasks.append(send_data_to_api(machine_id, data))
            else:
                print(f"No data found for today for machine {machine_id}")
        
        if tasks:
            await asyncio.gather(*tasks)
        
        await asyncio.sleep(INTERVAL.total_seconds())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    default_directory = os.getcwd()
    parser.add_argument("--script_dir", type=str, default=default_directory, help="Directory containing setup_database.py")
    args = parser.parse_args()

    asyncio.run(main(args.script_dir))
