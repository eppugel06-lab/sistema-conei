import os

class Config:
    # 🔑 Llave secreta (usar variable de entorno en producción)
    SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta")

    # 📂 Ruta de la base de datos SQLite
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE = os.path.join(BASE_DIR, "sistema_conei.db")

    # 🔧 Puedes agregar más configuraciones aquí (ej. debug, logs, etc.)
    DEBUG = os.getenv("DEBUG", "True") == "True"
