import sqlite3
import requests
import json

def create_database():
    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            location TEXT,
            mill TEXT,
            last_online TEXT,
            status TEXT,
            coordinate TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pengawasan_operator (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            machine_id INTEGER,
            uptime TEXT,
            FOREIGN KEY (machine_id) REFERENCES machine(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unattended (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pengawasan INTEGER,
            datetime TEXT,
            bot TEXT,
            FOREIGN KEY (id_pengawasan) REFERENCES pengawasan_operator(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snooze_bot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            description TEXT,
            hour INTEGER,
            machine_id INTEGER,
            user TEXT,
            no_hp TEXT,
            FOREIGN KEY (machine_id) REFERENCES machine(id)
        )
    ''')
    
    # Fetch data from API
    api_url = "https://srs-ssms.com/op_monitoring/get_list_machine.php"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        machines = json.loads(response.text)
        
        # Insert or update machine data
        for machine in machines:
            cursor.execute('''
                INSERT OR REPLACE INTO machine 
                (id, name, description, location, mill, last_online, status, coordinate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                machine['id'], machine['name'], machine['description'], 
                machine['location'], machine['mill'], machine['last_online'], 
                machine['status'], machine['coordinate']
            ))
        
        print("Machine data updated successfully.")
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        print("Database setup completed without updating machine data.")
    except json.JSONDecodeError:
        print("Error decoding JSON from API response.")
        print("Database setup completed without updating machine data.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Database setup completed without updating machine data.")
    
    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    create_database()
