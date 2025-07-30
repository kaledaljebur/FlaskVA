from flask import request, render_template
import sqlite3
from config import SECURITY_LEVEL

def run():
    result = ''
    if request.method == 'POST':
        uid = request.form['userid']
        conn = sqlite3.connect('db/flaskva.db')
        c = conn.cursor()

        if SECURITY_LEVEL == 'low':
            query = f"SELECT username FROM users WHERE id = {uid}"
        elif SECURITY_LEVEL == 'medium':
            uid = uid.replace("'", "")
            query = f"SELECT username FROM users WHERE id = '{uid}'"
        elif SECURITY_LEVEL == 'high':
            query = "SELECT username FROM users WHERE id = ?"
        else:
            try:
                uid = int(uid)
                query = "SELECT username FROM users WHERE id = ?"
            except:
                return render_template('sqli.html', result='Invalid input')

        try:
            if SECURITY_LEVEL in ['high', 'impossible']:
                c.execute(query, (uid,))
            else:
                c.execute(query)
            result = c.fetchone()
            result = result[0] if result else 'No result'
        except Exception as e:
            result = str(e)
    return render_template('sqli.html', result=result)