from flask import Flask, redirect, url_for
from routes.reconocimiento import reconocimiento_bp
from routes.detalle_ie import detalle_ie_bp
from routes.expedientes import expedientes_bp
from routes.reportes import reportes_bp
from routes.auth import auth_bp

# 🔧 Inicializar la app Flask
app = Flask(__name__)

# Cargar configuraciones desde config.py
app.config.from_object("config.Config")

# Registrar blueprints con prefijos de ruta
app.register_blueprint(reconocimiento_bp, url_prefix="/reconocimiento")
app.register_blueprint(detalle_ie_bp, url_prefix="/detalle-ie")
app.register_blueprint(expedientes_bp, url_prefix="/expedientes")
app.register_blueprint(reportes_bp, url_prefix="/reportes")
app.register_blueprint(auth_bp, url_prefix="/auth")

# 👉 Redirigir raíz (/) al login
@app.route("/")
def home():
    return redirect(url_for("auth.login"))

# 🔹 PythonAnywhere / Producción: se usa WSGI (no app.run())
if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])