import os
import io
import sqlite3
from flask import Blueprint, request, session, redirect, url_for, flash, current_app, send_file
from docx import Document
from datetime import date
from conexion_db import conectar
from routes.auth import login_required
from utils.drive import subir_pdf_a_drive, eliminar_archivo_drive
from PyPDF2 import PdfReader, PdfWriter

expedientes_bp = Blueprint("expedientes", __name__)

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
        # ---------------- DATOS FORM ----------------
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

        datos_ie_id = int(datos_ie_id) if datos_ie_id else None
        expediente_id = int(expediente_id) if expediente_id else None

        drive_file_id = None
        nuevo_nombre_pdf = None

        # ==========================================================
        # ====================== ACTUALIZAR ========================
        # ==========================================================
        if expediente_id:
            cursor.execute("""
                SELECT e.pdf_resolucion, e.drive_file_id, di.modalidad, di.codigo_local
                FROM expediente e
                JOIN datos_ie di ON e.datos_ie_id = di.id
                WHERE e.id = ?
            """, (expediente_id,))
            expediente_actual = cursor.fetchone()

            if not expediente_actual:
                raise Exception("Expediente no encontrado")

            modalidad = expediente_actual["modalidad"]
            codigo_local = expediente_actual["codigo_local"]
            drive_anterior = expediente_actual["drive_file_id"]

            # 🔑 conservar valores actuales
            nuevo_nombre_pdf = expediente_actual["pdf_resolucion"]
            drive_file_id = drive_anterior

            # ==================================================
            # SOLO SI SE SUBE UN PDF NUEVO
            # ==================================================
            if archivo_pdf and allowed_file(archivo_pdf.filename):

                # ---------- ELIMINAR PDF DRIVE ----------
                if drive_anterior:
                    try:
                        eliminar_archivo_drive(drive_anterior)
                    except Exception as e:
                        flash(f"No se pudo eliminar PDF anterior en Drive: {e}", "warning")

                extension = archivo_pdf.filename.rsplit(".", 1)[1].lower()
                nuevo_nombre_pdf = f"{modalidad}_{codigo_local}_RD_{n_resolucion}.{extension}"

                # 💾 PDF temporal en memoria con páginas seleccionadas
                pdf_bytes = guardar_pdf_por_paginas(archivo_pdf, pagina_inicio, pagina_fin)

                # ---------- SUBIR A DRIVE ----------
                drive_file_id = subir_pdf_a_drive(
                    pdf_bytes, nuevo_nombre_pdf, modalidad, codigo_local
                )

            # ==================================================
            # UPDATE FINAL
            # ==================================================
            cursor.execute("""
                UPDATE expediente
                SET fecha_registro=?, num_expediente=?, tipo_atencion=?, anio_inicio=?, anio_fin=?, estado=?,
                    fecha_emision=?, n_resolucion=?, pdf_resolucion=?, nombre_pdf=?, drive_file_id=?,
                    nombre_director=?, genero=?, correo=?, oficio_ie=?, detalle=?
                WHERE id=?
            """, (
                fecha_registro, num_expediente, tipo_atencion, anio_inicio, anio_fin, estado,
                fecha_emision, n_resolucion, nuevo_nombre_pdf, nuevo_nombre_pdf, drive_file_id,
                nombre_director, genero, correo, oficio_ie, detalle, expediente_id
            ))

        # ==========================================================
        # ======================== CREAR ===========================
        # ==========================================================
        else:
            if archivo_pdf and allowed_file(archivo_pdf.filename):
                extension = archivo_pdf.filename.rsplit(".", 1)[1].lower()
                nuevo_nombre_pdf = f"{modalidad}_{codigo_local}_RD_{n_resolucion}.{extension}"

                # 💾 PDF temporal en memoria
                pdf_bytes = guardar_pdf_por_paginas(archivo_pdf, pagina_inicio, pagina_fin)

                # ---------- SUBIR A DRIVE ----------
                drive_file_id = subir_pdf_a_drive(
                    pdf_bytes, nuevo_nombre_pdf, modalidad, codigo_local
                )

            cursor.execute("""
                INSERT INTO expediente (
                    fecha_registro, num_expediente, tipo_atencion, anio_inicio, anio_fin, estado,
                    fecha_emision, n_resolucion, pdf_resolucion, nombre_pdf, drive_file_id,
                    nombre_director, genero, correo, oficio_ie, detalle,
                    datos_ie_id, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha_registro, num_expediente, tipo_atencion, anio_inicio, anio_fin, estado,
                fecha_emision, n_resolucion, nuevo_nombre_pdf, nuevo_nombre_pdf, drive_file_id,
                nombre_director, genero, correo, oficio_ie, detalle,
                datos_ie_id, usuario_id
            ))

        conexion.commit()
        flash("Resolución registrada correctamente", "success")

    except Exception as e:
        conexion.rollback()
        flash(f"Error: {e}", "danger")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("detalle_ie.detalle_ie", datos_ie_id=datos_ie_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_pdf_por_paginas(archivo_pdf, pagina_inicio=None, pagina_fin=None):
    """Devuelve un PDF en memoria (io.BytesIO) con solo las páginas seleccionadas"""
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

    pdf_bytes = io.BytesIO()
    escritor.write(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes

@expedientes_bp.route("/eliminar_expediente/<int:expediente_id>", methods=["POST"])
@login_required
def eliminar_expediente(expediente_id):
    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
            e.drive_file_id,
            di.modalidad,
            di.codigo_local
        FROM expediente e
        JOIN datos_ie di ON e.datos_ie_id = di.id
        WHERE e.id = ?
    """, (expediente_id,))
    
    resultado = cursor.fetchone()

    if resultado:
        drive_file_id = resultado["drive_file_id"]

        # -----------------------------
        # ELIMINAR PDF EN DRIVE
        # -----------------------------
        try:
            if drive_file_id:
                eliminar_archivo_drive(drive_file_id)
        except Exception as e:
            # No bloquea el borrado en BD
            print("Error al eliminar archivo en Drive:", e)

        # -----------------------------
        # ELIMINAR REGISTRO BD
        # -----------------------------
        cursor.execute("DELETE FROM expediente WHERE id = ?", (expediente_id,))
        conexion.commit()

        flash("Expediente eliminado correctamente", "success")

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