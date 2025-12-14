from flask import Flask, render_template_string
import random

app = Flask(__name__)

HTML = open('index.html').read()

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/data')
def data():
    import json
    temp = round(20 + random.uniform(-5, 10), 2)
    hum = round(50 + random.uniform(-20, 30), 2)
    return json.dumps({
        'temperature': temp,
        'humidite': hum,
        'alerte': temp > 28
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)