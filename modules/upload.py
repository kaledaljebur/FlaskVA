from flask import request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'static/uploads'
# ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'php', 'html', 'py', 'sh'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return render_template('upload.html', filename=filename)
        return render_template('upload.html', error="Invalid file or extension")
    return render_template('upload.html')
