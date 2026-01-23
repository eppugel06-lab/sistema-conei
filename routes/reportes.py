from flask import Blueprint, render_template, jsonify, send_file
from conexion_db import conectar
import sqlite3
import datetime, io
from routes.auth import login_required
from openpyxl import Workbook

reportes_bp = Blueprint("reportes", __name__)

@reportes_bp.route("/reporte")
@login_required
def reporte():
    return render_template("reporte.html", pagina='reporte')


@reportes_bp.route("/api/reporte/<int:anio>")
@login_required
def api_reporte(anio):
    if anio == 0:
        anio = datetime.datetime.now().year

    conexion = conectar()
    if conexion is None:
        return jsonify({"error": "No se pudo conectar"}), 500

    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Total IIEE públicas
    cursor.execute("""
        SELECT COUNT(DISTINCT id) AS total 
        FROM datos_ie 
        WHERE gestion='ESTATAL'
    """)
    modalidad_estado = dict(cursor.fetchone())

    # Validados / Observados / Omisos
    cursor.execute("""
        SELECT COALESCE(e.estado, 'Omiso') AS estado,
               COUNT(DISTINCT d.id) AS total
        FROM datos_ie d
        LEFT JOIN expediente e
            ON e.datos_ie_id = d.id
            AND ? BETWEEN e.anio_inicio AND e.anio_fin
        WHERE d.gestion='ESTATAL'
        GROUP BY estado
    """, (anio,))
    validados_observados = [dict(r) for r in cursor.fetchall()]

    # Histórico
    cursor.execute("""
        SELECT anio, COUNT(DISTINCT datos_ie_id) AS total
        FROM (
            SELECT datos_ie_id, anio_inicio AS anio FROM expediente
            UNION ALL
            SELECT datos_ie_id, anio_fin AS anio FROM expediente
        )
        WHERE anio BETWEEN 2018 AND ?
        GROUP BY anio
        ORDER BY anio
    """, (datetime.datetime.now().year,))
    historico = [dict(r) for r in cursor.fetchall()]

    return jsonify({
        "anio": anio,
        "anio_actual": datetime.datetime.now().year,
        "modalidad_estado": modalidad_estado,
        "validados_observados": validados_observados,
        "historico": historico
    })


@reportes_bp.route("/reporte/exportar/<int:anio>")
@login_required
def exportar_reporte(anio):
    conexion = conectar()
    if conexion is None:
        return "❌ Error al conectar con la base de datos", 500

    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
            e.fecha_registro,
            d.codigo_local,
            d.institucion_educativa,
            d.modalidad,
            e.num_expediente,
            e.tipo_atencion,
            CASE 
                WHEN e.anio_inicio = e.anio_fin THEN e.anio_inicio
                ELSE e.anio_inicio || '-' || e.anio_fin
            END AS periodo,
            e.nombre_director,
            e.genero,
            e.estado,
            e.n_resolucion,
            e.fecha_emision,
            e.correo,
            e.oficio_ie,
            e.detalle
        FROM datos_ie d
        JOIN expediente e ON e.datos_ie_id = d.id
        ORDER BY d.institucion_educativa
    """)
    rows = cursor.fetchall()
    cursor.close()
    conexion.close()

    # 📗 Crear Excel en memoria
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"

    headers = [
        "Fecha Registro", "Código Local", "Institución Educativa", "Modalidad",
        "N° Expediente", "Tipo Atención", "Periodo", "Director",
        "Género", "Estado", "Resolución", "Fecha Emisión",
        "Correo", "Oficio IE", "Detalle"
    ]
    ws.append(headers)

    for r in rows:
        ws.append([
            r["fecha_registro"],
            r["codigo_local"],
            r["institucion_educativa"],
            r["modalidad"],
            r["num_expediente"],
            r["tipo_atencion"],
            r["periodo"],
            r["nombre_director"],
            r["genero"],
            r["estado"],
            r["n_resolucion"],
            r["fecha_emision"],
            r["correo"],
            r["oficio_ie"],
            r["detalle"],
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"reporte_{anio}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )