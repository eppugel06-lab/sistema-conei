from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from conexion_db import conectar
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        app_user = request.form.get("app_user", "").strip()
        password = request.form.get("password", "").strip()

        conexion = conectar()
        conexion.row_factory = __import__("sqlite3").Row  # 👈 resultados como diccionarios
        cursor = conexion.cursor()

        # ⚡ Usar `?` en SQLite (NO `%s`)
        cursor.execute("SELECT * FROM user WHERE app_user = ?", (app_user,))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        if user:
            if not user["activo"]:  # campo debe ser INTEGER 0/1
                flash("Usuario inactivo. Contacte con el administrador.", "warning")
            elif check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["user_name"] = user["user_name"]
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

