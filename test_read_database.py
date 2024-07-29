import sqlite3
import datetime

def read_database():
    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pengawasan_operator   LIMIT 10")
    rows = cursor.fetchall()

    print("Last 10 entries in the machine table:")
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Date: {row[1]}")
        print(f"Date: {row[2]}")
        print(f"Date: {row[3]}")
        # print(f"Machine ID: {row[2]}")
        # print(f"Uptime: {datetime.timedelta(seconds=row[3])}")
        # print("---")

    conn.close()

if __name__ == "__main__":
    read_database()
