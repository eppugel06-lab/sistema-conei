from flask import Blueprint, render_template
from datetime import datetime
import sqlite3
from conexion_db import conectar
from routes.auth import login_required

detalle_ie_bp = Blueprint('detalle_ie', __name__)

MODALIDAD_MAP = {
    "EBR": "I.E.",
    "EBA": "CEBA",
    "EBE": "CEBE",
    "ETP": "CETPRO"
}

@detalle_ie_bp.route('/detalle-ie/<int:datos_ie_id>')
@login_required
def detalle_ie(datos_ie_id):
    conexion = conectar()
    if conexion is None:
        return "❌ Error al conectar con la base de datos", 500

    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # 📌 Datos de la IE
    cursor.execute("SELECT * FROM datos_ie WHERE id = ? LIMIT 1", (datos_ie_id,))
    datos_ie = cursor.fetchone()
    if not datos_ie:
        cursor.close()
        conexion.close()
        return "❌ IE no encontrada", 404

    # 📌 Expedientes
    cursor.execute("""
        SELECT *
        FROM expediente
        WHERE datos_ie_id = ?
        ORDER BY fecha_emision DESC, estado ASC
    """, (datos_ie_id,))
    expedientes = cursor.fetchall()

    # 📌 Año actual
    anio_actual = datetime.now().year

    expedientes_normalizados = []
    for e in expedientes:
        exp_dict = dict(e)
        vigente = False

        if exp_dict["fecha_emision"]:
            try:
                fecha_str = exp_dict["fecha_emision"]

                # 🛠️ Quitar hora si existe
                if isinstance(fecha_str, str):
                    fecha_str = fecha_str.split(" ")[0]

                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                exp_dict["fecha_emision"] = fecha

                vigente = fecha.year in (anio_actual, anio_actual - 1)

            except Exception as e:
                print("⚠️ Error fecha_emision:", exp_dict["fecha_emision"], e)
                exp_dict["fecha_emision"] = None
                vigente = False

        exp_dict["vigente"] = vigente
        expedientes_normalizados.append(exp_dict)

    # 📌 NEXUS
    cursor.execute("""
        SELECT 
            nivel_educativo,
            codigo_modular,
            SUM(CASE WHEN cargo = 'DIRECTOR I.E.' THEN 1 ELSE 0 END) AS director_ie,
            SUM(CASE WHEN cargo = 'SUB-DIRECTOR I.E.' THEN 1 ELSE 0 END) AS subdirector_ie,
            SUM(CASE WHEN tipo_trabajador = 'DOCENTE' 
                     AND estado != 'ENCARGATURA DE FUNCIONES DE DIRECTOR' THEN 1 ELSE 0 END) AS docente,
            SUM(CASE WHEN estado = 'ENCARGATURA DE FUNCIONES DE DIRECTOR' THEN 1 ELSE 0 END) AS docente_dirige,
            SUM(CASE WHEN cargo = 'AUXILIAR DE EDUCACION' THEN 1 ELSE 0 END) AS auxiliar,
            SUM(CASE WHEN tipo_trabajador = 'ADMINISTRATIVO' THEN 1 ELSE 0 END) AS administrativo
        FROM nexus
        WHERE codigo_local = ? AND modalidad = ?
        GROUP BY nivel_educativo
    """, (datos_ie['codigo_local'], datos_ie['modalidad']))
    niveles_nexus = cursor.fetchall()

    # 📌 Totales base
    total_directores = sum(n["director_ie"] or 0 for n in niveles_nexus)
    total_subdirectores_real = sum(n["subdirector_ie"] or 0 for n in niveles_nexus)

    existe_auxiliar = any(n["auxiliar"] > 0 for n in niveles_nexus)
    existe_administrativo = any(n["administrativo"] > 0 for n in niveles_nexus)

    total_niveles = len(niveles_nexus)

    # =====================================================
    # 🟢 DECLARACIÓN DE INTEGRANTES DEL CONEI (NORMATIVA)
    # =====================================================

    normativa = 'ejemplo'

    # Presidente (Director)
    presidente = 1

    # Subdirectores
    if datos_ie["modalidad"] == "EBR":
        subdirectores = total_subdirectores_real
    else:
        subdirectores = 1 if total_directores > 0 else 0

    # Docentes (1 por nivel)
    docentes = total_niveles

    # Estudiantes (por nivel, sin Inicial EBR)
    niveles_inicial_ebr = {
        "Inicial - Jardín",
        "Inicial - Cuna-jardín",
        "Cuna-jardín"
    }

    estudiantes = 0
    for n in niveles_nexus:
        if not (
            datos_ie["modalidad"] == "EBR"
            and n["nivel_educativo"] in niveles_inicial_ebr
        ):
            estudiantes += 1

    # Familias
    familias = 1

    # Auxiliar / Administrativo
    auxiliar = 1 if existe_auxiliar else 0
    administrativo = 1 if existe_administrativo else 0

    # Total CONEI
    total_conei = (
        presidente +
        subdirectores +
        docentes +
        estudiantes +
        familias +
        auxiliar +
        administrativo
    )

    cursor.close()
    conexion.close()

    return render_template(
        "detalle_ie.html",
        datos_ie=datos_ie,
        anio_actual=anio_actual,
        normativa = normativa,
        expedientes=expedientes_normalizados,
        niveles_nexus=niveles_nexus,
        modalidad_map=MODALIDAD_MAP,

        # 👇 CONEI
        presidente=presidente,
        subdirectores=subdirectores,
        docentes=docentes,
        estudiantes=estudiantes,
        familias=familias,
        auxiliar=auxiliar,
        administrativo=administrativo,
        total_conei=total_conei
    )

