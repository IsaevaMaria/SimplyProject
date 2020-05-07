from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', title='Мой город - Кострома')

app.run(port=8080, host='127.0.0.1')
