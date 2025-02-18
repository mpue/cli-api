import streamlit as st
import requests
import os
import time
import re  # Für das Parsen des Bildpfads

FASTAPI_URL = "http://172.19.0.1:8000"  # Passe die URL an, falls FastAPI woanders läuft
UPLOAD_FOLDER = "/app/uploads"  # Blender speichert dort das gerenderte Bild
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.title("Streamlit FastAPI Interface")

# File Upload
st.header("Upload File")
uploaded_file = st.file_uploader("Choose a file", type=["blend", "csv", "json", "png", "jpg", "jpeg", "pdf"])  # Passe die Dateitypen an
if uploaded_file is not None:
    files = {'file': (uploaded_file.name, uploaded_file.getvalue())}  # Korrekte Übergabe des Dateinamens
    response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
    st.json(response.json())

# Command Execution mit Fortschrittsanzeige
default_command = "/blender -b uploads/default.blend --python gen.py -- --run"
st.header("Run Command")
command = st.text_input("Enter command", default_command)
filename = st.text_input("Filename (optional)")

# Fortschritt, Logs & Bildpfad im Session-State speichern
if "highest_progress" not in st.session_state:
    st.session_state.highest_progress = 0
if "log_output" not in st.session_state:
    st.session_state.log_output = ""  # Log zwischenspeichern
if "rendered_image" not in st.session_state:
    st.session_state.rendered_image = None  # Pfad zum fertigen Bild

progress_placeholder = st.empty()
status_text = st.empty()
log_placeholder = st.empty()
image_placeholder = st.empty()  # Platzhalter für das fertige Bild

def extract_progress(line):
    """
    Extrahiert den Fortschritt aus einer Blender-Log-Zeile.
    Beispiel: "Sample 256/4096" -> Fortschritt in Prozent.
    """
    if "Sample" in line:
        parts = line.split("Sample ")
        if len(parts) > 1:
            try:
                samples = parts[1].split("/")
                current_sample = int(samples[0])
                total_samples = int(samples[1])
                return int((current_sample / total_samples) * 100)
            except ValueError:
                return None
    return None

def extract_rendered_image(line):
    """
    Sucht nach dem Bildpfad in Blender-Logs.
    Beispiel-Log: "Saved: '/app/uploads/output.png'"
    """
    match = re.search(r"Saved:\s?'(.+?\.(png|jpg|jpeg|exr))'", line)
    if match:
        return match.group(1)
    return None

if st.button("Run Command"):
    data = {'command': command}
    if filename:
        data['filename'] = filename
    
    response = requests.post(f"{FASTAPI_URL}/run/", data=data, stream=True)

    if response.status_code == 200:
        st.session_state.highest_progress = 0  # Fortschritt zurücksetzen
        st.session_state.log_output = ""  # Log zurücksetzen
        st.session_state.rendered_image = None  # Bildpfad zurücksetzen

        # **Echtzeit-Update**
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode()
                st.session_state.log_output += decoded_line + "\n"  # Log aktualisieren

                # Fortschrittsbalken aktualisieren
                progress = extract_progress(decoded_line)
                if progress is not None:
                    st.session_state.highest_progress = max(st.session_state.highest_progress, progress)

                # **Bildpfad erkennen**
                img_path = extract_rendered_image(decoded_line)
                if img_path:
                    st.session_state.rendered_image = img_path  # Bildpfad speichern

                # **Live UI-Update ohne Duplicate-Key-Fehler**
                progress_placeholder.progress(st.session_state.highest_progress)
                status_text.text(f"Fortschritt: {st.session_state.highest_progress}%")
                log_placeholder.text_area("Render Log", st.session_state.log_output, height=300)

                time.sleep(0.1)  # Kurze Pause für flüssigere Updates

        st.success("Render abgeschlossen!")

        # **Warten, bis das Bild existiert**
        if st.session_state.rendered_image:
            image_path = st.session_state.rendered_image
            for _ in range(10):  # 10 Versuche, das Bild zu finden
                if os.path.exists(image_path):
                    break
                time.sleep(0.5)  # Warte 0.5 Sekunden pro Versuch

            # **Fertiges Bild anzeigen, falls vorhanden**
            if os.path.exists(image_path):
                image_placeholder.image(image_path, caption="Gerendertes Bild", use_column_width=True)
            else:
                st.warning(f"Das Bild wurde nicht gefunden: {image_path}")
        else:
            st.warning("Kein gerendertes Bild erkannt.")
    else:
        st.error(f"Fehler: {response.status_code} - {response.text}")

# File Download
st.header("Download File")
download_filename = st.text_input("Enter filename to download")
if st.button("Download File"):
    response = requests.get(f"{FASTAPI_URL}/download/{download_filename}", stream=True)
    if response.status_code == 200:
        filepath = os.path.join(UPLOAD_FOLDER, download_filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        with open(filepath, "rb") as file:
            st.download_button(label="Download", data=file, file_name=download_filename)
    else:
        st.error("File not found")
