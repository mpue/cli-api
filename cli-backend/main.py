from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse, FileResponse
import subprocess
import shlex
import os

app = FastAPI()

ALLOWED_COMMANDS = ["/blender"]  # Sicherstellen, dass nur Blender als Kommando erlaubt ist
UPLOAD_DIR = "/data/uploads"  # Verzeichnis für hochgeladene Dateien im Container
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Sicherstellen, dass das Upload-Verzeichnis existiert

def run_command_stream(command: str, filename: str = None):
    """ Führt einen Befehl aus und streamt den Output als Generator. """
    args = shlex.split(command)

    if args[0] not in ALLOWED_COMMANDS:
        yield "ERROR: Command not allowed\n"
        return

    # Falls eine Datei übergeben wurde, prüfen, ob sie existiert und den Pfad anhängen
    if filename:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            yield "ERROR: File not found\n"
            return
        args.append(file_path)

    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    for line in process.stdout:
        yield line  # Sendet jede Zeile direkt an den Client

    process.stdout.close()
    process.wait()

    if process.returncode != 0:
        yield f"ERROR: Command failed with code {process.returncode}\n"

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Datei hochladen und speichern
    """
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename, "filepath": file_location}

@app.post("/run/")
async def run_command(command: str = Form(...), filename: str = Form(None)):
    """
    CLI-Befehl ausführen (optional mit hochgeladener Datei als Argument) und den Output streamen
    """
    return StreamingResponse(run_command_stream(command, filename), media_type="text/plain")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Datei herunterladen
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

@app.get("/")
async def info():
    return "Go away!"
