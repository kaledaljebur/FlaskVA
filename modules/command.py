from flask import request, render_template
import os
from config import SECURITY_LEVEL

def execute():
    output = ''
    if request.method == 'POST':
        host = request.form['host']
        if SECURITY_LEVEL == 'low':
            cmd = f"ping -c 1 {host}"
        elif SECURITY_LEVEL == 'medium':
            cmd = f"ping -c 1 {host.split(';')[0]}"
        elif SECURITY_LEVEL == 'high':
            if host.isalpha():
                cmd = f"ping -c 1 {host}"
            else:
                return render_template('command.html', output='Invalid hostname')
        else:
            return render_template('command.html', output='Blocked')

        try:
            output = os.popen(cmd).read()
        except:
            output = 'Error running command'

    return render_template('command.html', output=output)