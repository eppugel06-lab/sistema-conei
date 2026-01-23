import sqlite3

with open("schema.sql", "r", encoding="utf-8") as f:
    schema = f.read()

conn = sqlite3.connect("sistema_conei.db")  # 👈 mismo nombre que en conexion_db.py
cursor = conn.cursor()
cursor.executescript(schema)

conn.commit()
conn.close()

print("✅ Base de datos inicializada en sistema_conei.db")

