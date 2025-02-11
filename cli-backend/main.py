from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
import subprocess
import shlex
import uuid
import os

app = FastAPI()

UPLOAD_DIR = "/app/uploads"  # Verzeichnis für hochgeladene Dateien im Container

# Sicherstellen, dass der Upload-Ordner existiert
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    CLI-Befehl ausführen (optional mit hochgeladener Datei als Argument)
    """
    try:
        args = shlex.split(command)

        # Falls eine Datei angegeben wurde, den absoluten Pfad an den Befehl hängen
        if filename:
            file_path = os.path.join(UPLOAD_DIR, filename)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            args.append(file_path)

        # Subprozess innerhalb des Containers ausführen
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)

        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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