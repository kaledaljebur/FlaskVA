from flask import request, session, redirect, render_template

def set_level():
    if request.method == 'POST':
        session['security'] = request.form.get('level', 'low')
        return redirect('/')
    return render_template('security.html', current=session.get('security', 'low'))