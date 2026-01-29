from flask import Blueprint, render_template
from conexion_db import conectar
from routes.auth import login_required

reconocimiento_bp = Blueprint('reconocimiento', __name__)

MODALIDAD_MAP = {
    "EBR": "I.E.",
    "EBA": "CEBA",
    "EBE": "CEBE",
    "ETP": "CETPRO"
}

@reconocimiento_bp.route('/reconocimiento')
@login_required
def reconocimiento():
    conexion = conectar()
    if conexion is None:
        return "❌ Error al conectar con la base de datos", 500
    
    # Para obtener resultados como diccionarios
    conexion.row_factory = lambda cursor, row: {
        col[0]: row[idx] for idx, col in enumerate(cursor.description)
    }

    with conexion:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT 
                ie.id,
                ie.codigo_local,
                ie.institucion_educativa,
                ie.modalidad,
                CASE 
                    WHEN SUM(e.estado = 'Validado' and e.anio_fin = '2026') > 0 THEN 'Consolidado'
                    ELSE 'Sin Consolidar'
                END AS estado
            FROM datos_ie ie
            LEFT JOIN expediente e 
                ON ie.id = e.datos_ie_id
            GROUP BY ie.id, ie.codigo_local, ie.institucion_educativa, ie.modalidad
            ORDER BY ie.codigo_local, ie.modalidad
        """)
        datos = cursor.fetchall()

    return render_template(
        "reconocimiento.html",
        pagina='reconocimiento',
        datos=datos,
        modalidad_map=MODALIDAD_MAP
    )