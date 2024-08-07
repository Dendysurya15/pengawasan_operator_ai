import sqlite3

def read_database():
    conn = sqlite3.connect('operator_behaviour.db')
    cursor = conn.cursor()

    # Get column information
    cursor.execute("PRAGMA table_info(machine)")
    columns = cursor.fetchall()

    print("Column information for the 'pengawasan_operator' table:")
    for col in columns:
        cid, name, type, notnull, default_value, pk = col
        print(f"- Column {cid} ('{name}') - Type: {type}, Not Null: {bool(notnull)}, Primary Key: {bool(pk)}, Default Value: {default_value}")

    print("\nLast 10 entries in the 'pengawasan_operator' table:")
    cursor.execute("SELECT * FROM machine LIMIT 10")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    read_database()
