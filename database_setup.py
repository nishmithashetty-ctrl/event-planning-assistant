import sqlite3
from datetime import datetime

conn = sqlite3.connect("event_planning.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS moderators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    description TEXT,
    email TEXT,
    phone TEXT,
    expertise TEXT,
    created_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    role TEXT,
    phone TEXT,
    created_at TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ Database created successfully")
