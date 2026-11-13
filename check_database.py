import sqlite3

connection = sqlite3.connect("healthcoach.db")
cursor = connection.cursor()

# Show all database tables
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table'
""")

tables = cursor.fetchall()

print("\nDATABASE TABLES:")
for table in tables:
    print("\nTable:", table[0])

    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()

    print("Columns:")
    for column in columns:
        print("-", column[1])

connection.close()
