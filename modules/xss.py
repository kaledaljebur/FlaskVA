from flask import request, render_template

def reflect():
    q = request.args.get('q', '')
    return render_template('xss.html', input=q)