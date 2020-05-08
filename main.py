from flask import Flask, render_template
import os


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', title='Мой город - Кострома')

iport = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=iport)