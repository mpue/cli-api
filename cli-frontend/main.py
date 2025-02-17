import streamlit as st
import requests
import os

FASTAPI_URL = "http://172.19.0.1:8000"  # Passe die URL an, falls FastAPI woanders läuft
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.title("Streamlit FastAPI Interface")

# File Upload
st.header("Upload File")
uploaded_file = st.file_uploader("Choose a file", type=["blend", "csv", "json", "png", "jpg", "jpeg", "pdf"])  # Passe die Dateitypen an
if uploaded_file is not None:
    files = {'file': (uploaded_file.name, uploaded_file.getvalue())}  # Korrekte Übergabe des Dateinamens
    response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
    st.json(response.json())

# Command Execution
st.header("Run Command")
command = st.text_input("Enter command")
filename = st.text_input("Filename (optional)")
if st.button("Run Command"):
    data = {'command': command}
    if filename:
        data['filename'] = filename
    response = requests.post(f"{FASTAPI_URL}/run/", data=data)
    st.json(response.json())

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
