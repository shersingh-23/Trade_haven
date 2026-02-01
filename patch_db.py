import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("ALTER TABLE users ADD COLUMN reset_code TEXT;")
conn.commit()
conn.close()

print("✅ Done.")
