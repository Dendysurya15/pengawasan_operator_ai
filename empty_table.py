import sqlite3

def empty_table():
    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM pengawasan_operator")
    
    conn.commit()
    conn.close()
    print("Table pengawasan_operator has been emptied successfully.")

if __name__ == "__main__":
    empty_table()
