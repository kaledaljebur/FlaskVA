from flask import Flask, render_template, request, redirect, session, url_for
from config import SECRET_KEY, SECURITY_LEVEL
from modules import auth, sqli, upload, command, xss, ssrf, idor, security

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route('/')
def index():
    return render_template('index.html', security=session.get('security', 'low'))

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth.login()

@app.route('/sqli', methods=['GET', 'POST'])
def sqli_route():
    return sqli.run()

@app.route('/upload', methods=['GET', 'POST'])
def upload_route():
    return upload.handle()

@app.route('/command', methods=['GET', 'POST'])
def command_route():
    return command.execute()

@app.route('/xss', methods=['GET', 'POST'])
def xss_route():
    return xss.reflect()

@app.route('/ssrf', methods=['GET', 'POST'])
def ssrf_route():
    return ssrf.request_url()

@app.route('/idor')
def idor_route():
    return idor.view()

@app.route('/security', methods=['GET', 'POST'])
def security_route():
    return security.set_level()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
