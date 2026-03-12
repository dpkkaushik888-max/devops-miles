import sqlite3

conn = sqlite3.connect('names.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS names (id INTEGER PRIMARY KEY, name TEXT)')
conn.commit()
conn.close()
print("Database migrated.")
