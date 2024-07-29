import sqlite3
import requests
import json

def create_database():
    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create the 'machine' table
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
    
    # Create the 'pengawasan_operator' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pengawasan_operator (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            machine_id INTEGER,
            uptime TEXT,
            FOREIGN KEY (machine_id) REFERENCES machine(id)
        )
    ''')

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

    conn.commit()
    conn.close()
    print("Database setup complete with new tables.")

if __name__ == "__main__":
    create_database()
