from flask import request, render_template

def view():
    file_id = request.args.get('file', '1')
    return render_template('idor.html', file=file_id)