from flask import Blueprint, render_template
from conexion_db import conectar
from routes.auth import login_required
from datetime import datetime

reconocimiento_bp = Blueprint('reconocimiento', __name__)

MODALIDAD_MAP = {
    "EBR": "IE",
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

    anio_actual = datetime.now().year
    
    with conexion:
        cursor = conexion.cursor()
        cursor.execute("""
                        SELECT 
                            ie.id,
                            ie.codigo_local,
                            ie.institucion_educativa,
                            ie.modalidad,
                            CASE 
                                WHEN e.estado IS NOT NULL THEN e.estado
                                ELSE 'Sin Registro'
                            END AS estado
                        FROM datos_ie ie
                        LEFT JOIN expediente e 
                            ON ie.id = e.datos_ie_id
                        AND e.anio_fin = ?
                        ORDER BY ie.codigo_local, ie.modalidad
                    """, (anio_actual,))
        datos = cursor.fetchall()

    return render_template(
        "reconocimiento.html",
        pagina='reconocimiento',
        datos=datos,
        anio_actual=anio_actual,
        modalidad_map=MODALIDAD_MAP
    )