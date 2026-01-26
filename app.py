from flask import Flask, redirect, url_for, request, current_app
from routes.reconocimiento import reconocimiento_bp
from routes.detalle_ie import detalle_ie_bp
from routes.expedientes import expedientes_bp
from routes.reportes import reportes_bp
from routes.auth import auth_bp
import os
# ⚠️ SOLO PARA DESARROLLO LOCAL
if os.getenv("FLASK_ENV") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google_auth_oauthlib.flow import Flow


# ======================================================
# 🔧 Inicializar Flask
# ======================================================
app = Flask(__name__)
app.config.from_object("config.Config")


# ======================================================
# 🔑 LOGIN GOOGLE DRIVE (UNA SOLA VEZ)
# ======================================================
@app.route("/login_drive")
def login_drive():
    flow = Flow.from_client_secrets_file(
        current_app.config["CLIENT_SECRETS_FILE"],
        scopes=current_app.config["SCOPES"],
        redirect_uri=current_app.config["REDIRECT_URI"]
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"  # ⚠️ solo se usa la primera vez
    )

    return redirect(auth_url)


# ======================================================
# 🔄 CALLBACK OAUTH
# ======================================================
@app.route("/oauth2callback")
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        current_app.config["CLIENT_SECRETS_FILE"],
        scopes=current_app.config["SCOPES"],
        redirect_uri=current_app.config["REDIRECT_URI"]
    )

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    # 💾 Guardar token reutilizable
    with open(current_app.config["TOKEN_FILE"], "w") as token:
        token.write(creds.to_json())

    return "✅ Google Drive autorizado correctamente. Ya puedes cerrar esta pestaña."


# ======================================================
# 📦 BLUEPRINTS
# ======================================================
app.register_blueprint(reconocimiento_bp, url_prefix="/reconocimiento")
app.register_blueprint(detalle_ie_bp, url_prefix="/detalle-ie")
app.register_blueprint(expedientes_bp, url_prefix="/expedientes")
app.register_blueprint(reportes_bp, url_prefix="/reportes")
app.register_blueprint(auth_bp, url_prefix="/auth")


# ======================================================
# 👉 RUTA RAÍZ
# ======================================================
@app.route("/")
def home():
    return redirect(url_for("auth.login"))


# ======================================================
# ▶️ LOCAL / PYTHONANYWHERE
# ======================================================
if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
