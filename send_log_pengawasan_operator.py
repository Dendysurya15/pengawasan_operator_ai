import requests
import sqlite3
import time
from datetime import date, datetime, timedelta

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

def main():
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

if __name__ == "__main__":
    main()
