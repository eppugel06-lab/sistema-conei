import os
import io
from flask import current_app
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from PyPDF2 import PdfReader, PdfWriter

# ======================================================
# 🚀 SERVICIO GOOGLE DRIVE (USA TOKEN EXISTENTE)
# ======================================================
def get_drive_service():
    token_file = current_app.config["TOKEN_FILE"]
    scopes = current_app.config["SCOPES"]

    if not os.path.exists(token_file):
        raise Exception("Google Drive no autorizado. Visita /login_drive primero.")

    creds = Credentials.from_authorized_user_file(token_file, scopes)

    # 🔄 Refrescar automáticamente
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # 💾 Guardar token actualizado
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ======================================================
# 📁 BUSCAR CARPETA EXISTENTE
# ======================================================
def buscar_carpeta(service, nombre_carpeta, carpeta_padre_id=None):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{nombre_carpeta}'"
    if carpeta_padre_id:
        query += f" and '{carpeta_padre_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get("files", [])
    return items[0]["id"] if items else None


# ======================================================
# 🗑️ ELIMINAR ARCHIVO EN DRIVE
# ======================================================
def eliminar_archivo_drive(file_id):
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()


# ======================================================
# 📤 SUBIR PDF A DRIVE DESDE MEMORIA
# ======================================================
def subir_pdf_a_drive(file_obj, nombre_archivo, ie_modalidad, ie_codigo, pagina_inicio=None, pagina_fin=None):
    """
    file_obj: archivo recibido desde Flask (request.files['archivo_rd'])
    nombre_archivo: nombre para Google Drive
    pagina_inicio/pagina_fin: rango de páginas a extraer (opcional)
    """
    service = get_drive_service()
    base_id = current_app.config["CONEI_BASE_FOLDER_ID"]

    subcarpeta_nombre = f"{ie_modalidad}_{ie_codigo}"
    subcarpeta_id = buscar_carpeta(service, subcarpeta_nombre, base_id)
    if not subcarpeta_id:
        raise ValueError(f"No existe la subcarpeta '{subcarpeta_nombre}' en Drive")

    # ----------------- CREAR PDF EN MEMORIA -----------------
    lector = PdfReader(file_obj)
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
    pdf_bytes.seek(0)  # reiniciar puntero

    # ----------------- SUBIR A DRIVE -----------------
    media = MediaIoBaseUpload(pdf_bytes, mimetype="application/pdf", resumable=True)
    file_metadata = {"name": nombre_archivo, "parents": [subcarpeta_id]}

    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")
