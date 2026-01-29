import os
from datetime import timedelta

class Config:
    # 🔑 Llave secreta (usar variable de entorno en producción)
    SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta")

    # 📂 Base de datos
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE = os.path.join(BASE_DIR, "sistema_conei.db")

    # 🐞 Debug
    DEBUG = os.getenv("DEBUG", "True") == "True"

    # ======================================================
    # 🔐 CONFIGURACIÓN OAUTH GOOGLE DRIVE
    # ======================================================
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    # credentials OAuth (tipo: Web application)
    CLIENT_SECRETS_FILE = os.getenv(
        "GOOGLE_CLIENT_SECRETS",
        r"C:\Users\Finanzas003\Desktop\CONEI\secrets\credentials-local.json"
    )

    # token generado automáticamente
    TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

    CONEI_BASE_FOLDER_ID = "1Ekt7zsSmzt4_o-18qToHzMYGdPgocqem"

    # 👉 Local
    REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:5000/oauth2callback"
    )

    # 👉 Producción (PythonAnywhere)
    # GOOGLE_REDIRECT_URI=https://TU_USUARIO.pythonanywhere.com/oauth2callback

     # ⏰ Tiempo máximo de inactividad (segundos)
    INACTIVITY_TIMEOUT = 900  # 15 minutos

    # Flask session lifetime (extra seguridad)
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=INACTIVITY_TIMEOUT)
