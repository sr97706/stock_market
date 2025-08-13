import sqlite3

# Connect to your database
conn = sqlite3.connect("stocks.db")
cursor = conn.cursor()

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in DB:", tables)

# Check if table exists
if ('stock_data',) in tables:
    cursor.execute("SELECT COUNT(*) FROM stock_data;")
    count = cursor.fetchone()[0]
    print(f"Total rows in stock_data: {count}")

    # Show 5 sample rows
    cursor.execute("SELECT * FROM stock_data LIMIT 5;")
    for row in cursor.fetchall():
        print(row)
else:
    print("❌ Table 'stock_data' does not exist.")

conn.close()

