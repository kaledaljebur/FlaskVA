from flask import Flask, render_template, request, redirect, session, url_for
from config import SECRET_KEY, SECURITY_LEVEL
from modules import auth, sqli, upload, command, xss, ssrf, idor, security

app = Flask(__name__)
app.secret_key = "siudhisuhgiubgidno23u09"
users = {"admin": "mustang"}

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
        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        else:
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
