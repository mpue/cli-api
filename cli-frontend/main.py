from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import requests
import os

app = Flask(__name__)
FASTAPI_URL = "http://172.19.0.1:8000"  # Passe die URL an, falls FastAPI woanders läuft
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template("ui.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        files = {'file': (file.filename, file)}  # Korrekte Übergabe des Dateinamens
        response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
        return jsonify(response.json())
    return redirect(url_for('index'))


@app.route('/run', methods=['POST'])
def run_command():
    command = request.form['command']
    filename = request.form.get('filename', '')
    data = {'command': command}
    if filename:
        data['filename'] = filename
    response = requests.post(f"{FASTAPI_URL}/run/", data=data)
    return render_template("ui.html", output=response.json())

@app.route('/download/<filename>')
def download_file(filename):
    response = requests.get(f"{FASTAPI_URL}/download/{filename}", stream=True)
    if response.status_code == 200:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    print ("startup.")
    app.run(debug=True, host='0.0.0.0', port=5000)
