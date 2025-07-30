from flask import request, render_template
import requests

def request_url():
    url = request.form.get('url') if request.method == 'POST' else ''
    response = ''
    if url:
        try:
            r = requests.get(url, timeout=2)
            response = r.text[:300]
        except: response = 'Error fetching URL'
    return render_template('ssrf.html', url=url, response=response)