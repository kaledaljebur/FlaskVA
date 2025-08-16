from flask import Flask, render_template, request, redirect, session, url_for, g
from config import SECRET_KEY, SECURITY_LEVEL
from modules import auth, sqli, upload, command, xss, ssrf, idor, security
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "siudhisuhgiubgidno23u09"
users = {"admin": "mustang"}

DB_CONFIG = {
    "host": "localhost",
    "user": "flaskva",
    "password": "flaskva",
    "database": "flaskva"
}

def get_db():
    if "db" not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template('index.html', security=session.get('security', 'low'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # return auth.login()
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cur.fetchone()

        if row:
            stored_password = row[0]
            if check_password_hash(stored_password, password):
                session["user"] = username
                return redirect(url_for("index"))

        # if username in users and users[username] == password:
        #     session["user"] = username
        #     return redirect(url_for("index"))
        # else:
            return render_template("login.html", error="Invalid login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/sqli', methods=['GET', 'POST'])
def sqli_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return sqli.run()

@app.route('/upload', methods=['GET', 'POST'])
def upload_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return upload.handle()

@app.route('/command', methods=['GET', 'POST'])
def command_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return command.execute()

@app.route('/xss', methods=['GET', 'POST'])
def xss_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return xss.reflect()

@app.route('/ssrf', methods=['GET', 'POST'])
def ssrf_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return ssrf.request_url()

@app.route('/idor')
def idor_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return idor.view()

@app.route('/security', methods=['GET', 'POST'])
def security_route():
    if "user" not in session:
        return redirect(url_for("login"))
    return security.set_level()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
