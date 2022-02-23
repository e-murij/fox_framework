import sqlite3
from components.settings import DATABASE

con = sqlite3.connect(DATABASE)
cur = con.cursor()
with open('create_db.sql', 'r') as f:
    text = f.read()
cur.executescript(text)
cur.close()
con.close()
