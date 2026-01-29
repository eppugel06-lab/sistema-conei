from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import check_password_hash
from conexion_db import conectar
from functools import wraps
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        app_user = request.form.get("app_user", "").strip()
        password = request.form.get("password", "").strip()

        conexion = conectar()
        conexion.row_factory = __import__("sqlite3").Row
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT * FROM user WHERE app_user = ?",
            (app_user,)
        )
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        if user:
            if not user["activo"]:
                flash("Usuario inactivo. Contacte con el administrador.", "warning")

            elif check_password_hash(user["password_hash"], password):
                session.clear()

                session["user_id"] = user["id"]
                session["user_name"] = user["user_name"]

                # ⏰ registrar actividad inicial
                session["last_activity"] = datetime.utcnow().timestamp()

                flash(f"Bienvenido {user['user_name']}", "success")
                return redirect(url_for("reconocimiento.reconocimiento"))

            else:
                flash("Contraseña incorrecta", "danger")
        else:
            flash("Usuario no encontrado", "danger")

    return render_template("login.html")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Debes iniciar sesión primero.", "warning")
            return redirect(url_for("auth.login"))

        now = datetime.utcnow().timestamp()
        last_activity = session.get("last_activity")

        # ⏱️ tiempo máximo (segundos)
        timeout = current_app.config.get("INACTIVITY_TIMEOUT", 900)

        if last_activity and (now - last_activity) > timeout:
            session.clear()
            flash("Sesión cerrada por inactividad.", "warning")
            return redirect(url_for("auth.login"))

        # 🔄 actualizar actividad
        session["last_activity"] = now

        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return f"Hola {session['user_name']}, estás dentro del sistema ✅"


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for("auth.login"))

