import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from utils.pdf_handler import get_pdf_fields, fill_pdf_form

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Pfade definieren
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, 'storage')
UPLOAD_FOLDER = os.path.join(STORAGE_DIR, 'templates')
PROFILE_FOLDER = os.path.join(STORAGE_DIR, 'profiles')
OUTPUT_FOLDER = os.path.join(STORAGE_DIR, 'output')

STIRLING_URL = os.environ.get('STIRLING_PDF_URL', 'http://192.168.178.20:8085')

@app.route('/')
def index():
    # Vorhandene PDFs und Profile auflisten
    pdfs = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    profiles = [f for f in os.listdir(PROFILE_FOLDER) if f.endswith('.json')]
    
    # Stirling PDF Status prüfen
    stirling_online = False
    try:
        response = requests.get(f"{STIRLING_URL}/api/v1/info", timeout=2)
        if response.status_code == 200:
            stirling_online = True
    except:
        pass

    return render_template('base.html', pdfs=pdfs, profiles=profiles, stirling_online=stirling_online, stirling_url=STIRLING_URL)

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        flash('Keine Datei hochgeladen', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['pdf_file']
    if file.filename == '':
        flash('Keine Datei ausgewählt', 'danger')
        return redirect(url_for('index'))
        
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        flash(f'PDF "{filename}" erfolgreich hochgeladen.', 'success')
    else:
        flash('Ungültiges Dateiformat. Nur PDFs erlaubt.', 'danger')
        
    return redirect(url_for('index'))

@app.route('/parse-pdf/<filename>')
def parse_pdf(filename):
    pdf_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    fields = get_pdf_fields(pdf_path)
    return jsonify({'fields': fields})

@app.route('/save-profile', methods=['POST'])
def save_profile():
    data = request.json
    profile_name = secure_filename(data.get('profile_name'))
    if not profile_name.endswith('.json'):
        profile_name += '.json'
        
    profile_path = os.path.join(PROFILE_FOLDER, profile_name)
    
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(data.get('fields'), f, ensure_ascii=False, indent=4)
        
    return jsonify({'status': 'success', 'message': f'Profil {profile_name} gespeichert.'})

@app.route('/load-profile/<filename>')
def load_profile(filename):
    profile_path = os.path.join(PROFILE_FOLDER, secure_filename(filename))
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({'error': 'Profil nicht gefunden'}), 404

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    pdf_name = request.form.get('selected_pdf')
    profile_data_raw = request.form.get('field_data')
    
    if not pdf_name or not profile_data_raw:
        flash('Fehlende Daten zur PDF-Generierung', 'danger')
        return redirect(url_for('index'))
        
    field_data = json.loads(profile_data_raw)
    
    source_path = os.path.join(UPLOAD_FOLDER, secure_filename(pdf_name))
    output_filename = f"filled_{secure_filename(pdf_name)}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
    try:
        fill_pdf_form(source_path, output_path, field_data)
        return send_from_directory(OUTPUT_FOLDER, output_filename, as_attachment=True)
    except Exception as e:
        flash(f'Fehler beim Befüllen der PDF: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8086, debug=False)
