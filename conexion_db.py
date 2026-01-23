import sqlite3
from config import Config

def conectar():
    try:
        conexion = sqlite3.connect(
            Config.DATABASE,
            check_same_thread=False
        )
        conexion.row_factory = sqlite3.Row
        print(f"✅ Conectado a SQLite: {Config.DATABASE}")
        return conexion
    except sqlite3.Error as e:
        print(f"❌ Error SQLite: {e}")
        return None
