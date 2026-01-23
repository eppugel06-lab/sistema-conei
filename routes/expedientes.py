import os, io
import sqlite3
from PyPDF2 import PdfReader, PdfWriter
from flask import Blueprint, request, session, redirect, url_for, flash, current_app, send_file
from docx import Document
from datetime import date
from conexion_db import conectar
from routes.auth import login_required

expedientes_bp = Blueprint("expedientes", __name__)

UPLOAD_FOLDER = "static/conei_pdf"
ALLOWED_EXTENSIONS = {"pdf"}

@expedientes_bp.route("/guardar_resolucion", methods=["POST"])
@login_required
def guardar_resolucion():
    datos_ie_id = None
    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    pagina_inicio = request.form.get("pagina_inicio")
    pagina_fin = request.form.get("pagina_fin")

    pagina_inicio = int(pagina_inicio) if pagina_inicio else None
    pagina_fin = int(pagina_fin) if pagina_fin else None

    try:
        # Datos del formulario
        fecha_registro = date.today().strftime("%Y-%m-%d")
        datos_ie_id = request.form.get("datos_ie_id")
        usuario_id = session["user_id"]
        expediente_id = request.form.get("expediente_id")
        codigo_local = request.form.get("codigo_local")
        modalidad = request.form.get("modalidad")
        nombre_director = request.form.get("director")
        genero = request.form.get("genero")
        num_expediente = request.form.get("expediente")
        tipo_atencion = request.form.get("tipo_atencion")
        anio_inicio = request.form.get("anio_inicio")
        anio_fin = request.form.get("anio_inicio")
        estado = request.form.get("estado")
        n_resolucion = request.form.get("resolucion_directoral")
        fecha_emision = request.form.get("fecha_emision")
        correo = request.form.get("correo", "")
        oficio_ie = request.form.get("oficio", "")
        detalle = request.form.get("detalle", "")
        archivo_pdf = request.files.get("archivo_rd")

        # Convertir a enteros
        datos_ie_id = int(datos_ie_id) if datos_ie_id else None
        usuario_id = int(usuario_id) if usuario_id else None
        expediente_id = int(expediente_id) if expediente_id else None

        if expediente_id:
            # --- ACTUALIZAR ---
            cursor.execute(
                """
                SELECT e.pdf_resolucion, di.modalidad, di.codigo_local 
                FROM expediente e 
                JOIN datos_ie di ON e.datos_ie_id = di.id 
                WHERE e.id = ?
                """,
                (expediente_id,),
            )
            expediente_actual = cursor.fetchone()

            if not expediente_actual:
                cursor.close()
                conexion.close()
                return "Expediente no encontrado", 404

            modalidad = expediente_actual["modalidad"]
            codigo_local = expediente_actual["codigo_local"]
            pdf_anterior = expediente_actual["pdf_resolucion"]

            # Manejo de PDFs
            nuevo_nombre_pdf = pdf_anterior
            carpeta_destino = os.path.join(
                current_app.root_path, UPLOAD_FOLDER, f"{modalidad}_{codigo_local}"
            )
            os.makedirs(carpeta_destino, exist_ok=True)

            if archivo_pdf and archivo_pdf.filename:
                # Eliminar anterior
                if pdf_anterior:
                    ruta_pdf_anterior = os.path.join(carpeta_destino, pdf_anterior)
                    if os.path.exists(ruta_pdf_anterior):
                        os.remove(ruta_pdf_anterior)
                # Guardar nuevo
                extension = archivo_pdf.filename.rsplit(".", 1)[1].lower()
                nuevo_nombre_pdf = f"{modalidad}_{codigo_local}_RD_{n_resolucion}.{extension}"

                ruta_pdf = os.path.join(carpeta_destino, nuevo_nombre_pdf)

                if pagina_inicio and pagina_fin and pagina_inicio > pagina_fin:
                    raise ValueError("La página inicial no puede ser mayor que la final")
                
                guardar_pdf_por_paginas(
                    archivo_pdf,
                    ruta_pdf,
                    pagina_inicio,
                    pagina_fin
                )

            cursor.execute(
                """
                UPDATE expediente
                SET fecha_registro=?, num_expediente=?, tipo_atencion=?, anio_inicio=?, anio_fin=?, estado=?,
                    fecha_emision=?, n_resolucion=?, pdf_resolucion=?, nombre_director=?,
                    genero=?, correo=?, oficio_ie=?, detalle=?
                WHERE id=?
                """,
                (
                    fecha_registro,
                    num_expediente,
                    tipo_atencion,
                    anio_inicio,
                    anio_fin,
                    estado,
                    fecha_emision,
                    n_resolucion,
                    nuevo_nombre_pdf,
                    nombre_director,
                    genero,
                    correo,
                    oficio_ie,
                    detalle,
                    expediente_id,
                ),
            )

        else:
            # --- CREAR ---
            archivo_nombre = None
            if archivo_pdf and allowed_file(archivo_pdf.filename):
                extension = archivo_pdf.filename.rsplit(".", 1)[1].lower()
                archivo_nombre = f"{modalidad}_{codigo_local}_RD_{n_resolucion}.{extension}"

                carpeta_destino = os.path.join(
                    current_app.root_path, UPLOAD_FOLDER, f"{modalidad}_{codigo_local}"
                )
                os.makedirs(carpeta_destino, exist_ok=True)

                ruta_pdf = os.path.join(carpeta_destino, archivo_nombre)

                if pagina_inicio and pagina_fin and pagina_inicio > pagina_fin:
                    raise ValueError("La página inicial no puede ser mayor que la final")

                guardar_pdf_por_paginas(
                    archivo_pdf,
                    ruta_pdf,
                    pagina_inicio,
                    pagina_fin
                )

            cursor.execute(
                """
                INSERT INTO expediente (
                    fecha_registro, num_expediente, tipo_atencion, anio_inicio, anio_fin, estado,
                    fecha_emision, n_resolucion, pdf_resolucion, nombre_director,
                    genero, correo, oficio_ie, detalle, datos_ie_id, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fecha_registro,
                    num_expediente,
                    tipo_atencion,
                    anio_inicio,
                    anio_fin,
                    estado,
                    fecha_emision,
                    n_resolucion,
                    archivo_nombre,
                    nombre_director,
                    genero,
                    correo,
                    oficio_ie,
                    detalle,
                    datos_ie_id,
                    usuario_id,
                ),
            )

        conexion.commit()
        flash("Resolución registrada correctamente", "success")

    except Exception as e:
        conexion.rollback()
        print("Error al registrar resolución:", e)
        flash(f"Error al registrar resolución: {e}", "danger")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("detalle_ie.detalle_ie", datos_ie_id=datos_ie_id))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def guardar_pdf_por_paginas(archivo_pdf, ruta_salida, pagina_inicio=None, pagina_fin=None):
    lector = PdfReader(archivo_pdf)
    escritor = PdfWriter()

    total_paginas = len(lector.pages)

    if pagina_inicio and pagina_fin:
        inicio = max(1, pagina_inicio)
        fin = min(pagina_fin, total_paginas)

        for i in range(inicio - 1, fin):
            escritor.add_page(lector.pages[i])
    else:
        for pagina in lector.pages:
            escritor.add_page(pagina)

    with open(ruta_salida, "wb") as f:
        escritor.write(f)

@expedientes_bp.route("/eliminar_expediente/<int:expediente_id>", methods=["POST"])
@login_required
def eliminar_expediente(expediente_id):
    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT e.pdf_resolucion, di.modalidad, di.codigo_local 
        FROM expediente e 
        JOIN datos_ie di ON e.datos_ie_id = di.id 
        WHERE e.id = ?
        """,
        (expediente_id,),
    )
    resultado = cursor.fetchone()

    if resultado:
        pdf_resolucion = resultado["pdf_resolucion"]
        modalidad = resultado["modalidad"]
        codigo_local = resultado["codigo_local"]

        if pdf_resolucion:
            carpeta_destino = os.path.join(
                current_app.root_path, UPLOAD_FOLDER, f"{modalidad}_{codigo_local}"
            )
            archivo_ruta = os.path.join(carpeta_destino, pdf_resolucion)
            if os.path.exists(archivo_ruta):
                os.remove(archivo_ruta)

        cursor.execute("DELETE FROM expediente WHERE id=?", (expediente_id,))
        conexion.commit()

    cursor.close()
    conexion.close()
    return redirect(request.referrer)


def reemplazar_etiquetas(doc, reemplazos):
    for p in doc.paragraphs:
        for run in p.runs:
            for clave, valor in reemplazos.items():
                if clave in run.text:
                    run.text = run.text.replace(clave, valor)


@expedientes_bp.route("/generar_oficio/<int:expediente_id>")
@login_required
def generar_oficio(expediente_id):
    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT e.num_expediente, e.tipo_atencion, e.estado, e.anio_inicio, 
               e.n_resolucion, e.nombre_director, e.genero, e.correo, e.oficio_ie, 
               e.detalle, d.distrito, d.institucion_educativa, d.modalidad, d.direccion_ie
        FROM expediente e 
        JOIN datos_ie d ON e.datos_ie_id = d.id 
        WHERE e.id = ?
        """,
        (expediente_id,),
    )
    expediente = cursor.fetchone()

    if not expediente:
        return "Expediente no encontrado", 404

    if expediente["estado"] == "Validado":
        plantilla_relativa = "static/plantillas/plantilla_oficio_validacion.docx"
    else:
        plantilla_relativa = "static/plantillas/plantilla_oficio_observacion.docx"

    plantilla = os.path.join(current_app.root_path, plantilla_relativa)

    # (opcional pero recomendado)
    if not os.path.exists(plantilla):
        return f"No se encontró la plantilla: {plantilla}", 500

    doc = Document(plantilla)

    map_modalidad = {
        "EBR": {"corto": "IE", "largo": "Institución Educativa"},
        "EBA": {"corto": "CEBA", "largo": "Centro de Educación Básica Alternativa"},
        "EBE": {"corto": "CEBE", "largo": "Centro de Educación Básica Especial"},
        "ETP": {"corto": "CETPRO", "largo": "Centro de Educación Técnico Productiva"},
    }
    modalidad_data = map_modalidad.get(
        expediente["modalidad"],
        {"corto": expediente["modalidad"], "largo": expediente["modalidad"]},
    )

    reemplazos = {
        "<<SR>>": "Sr" if expediente["genero"] == "Masculino" else "Sra",
        "<<DIRECTOR>>": "DIRECTOR" if expediente["genero"] == "Masculino" else "DIRECTORA",
        "<<NOMBRE>>": expediente["nombre_director"] or "",
        "<<MODALIDAD>>": modalidad_data["corto"] or "",
        "<<MODALIDAD_LARGO>>": modalidad_data["largo"],
        "<<IE>>": expediente["institucion_educativa"] or "",
        "<<DIRECCION_IE>>": expediente["direccion_ie"] or "",
        "<<DISTRITO>>": expediente["distrito"] or "",
        "<<CORREO>>": expediente["correo"] or "",
        "<<ATENCION_MAY>>": (expediente["tipo_atencion"] or "").upper(),
        "<<PERIODO>>": expediente["anio_inicio"] or "",
        "<<OFICIO>>": expediente["oficio_ie"] or "",
        "<<EXPEDIENTE>>": expediente["num_expediente"] or "",
        "<<SALUDO>>": "saludarlo" if expediente["genero"] == "Masculino" else "saludarla",
        "<<DETALLE>>": expediente["n_resolucion"] or "",
        "<<ATENCION_MIN>>": "reconoce"
        if expediente["tipo_atencion"] == "Reconocimiento"
        else "actualiza",
    }

    reemplazar_etiquetas(doc, reemplazos)

    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return send_file(
        file_stream,
        as_attachment=True,
        download_name=(
            f"Proyecto de Oficio del Exp. N° {expediente['num_expediente']} - "
            f"{modalidad_data['corto']} {expediente['institucion_educativa']}.docx"
        ),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )