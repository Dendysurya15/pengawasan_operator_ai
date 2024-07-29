import sqlite3
import requests
import json

def create_database():
    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Existing tables...

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

    # Rest of the existing code...

    conn.commit()
    conn.close()
    print("Database setup complete with new tables.")

if __name__ == "__main__":
    create_database()
