from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Usuario y contraseña de ejemplo
USERNAME = 'admin'
PASSWORD = '1234'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == USERNAME and password == PASSWORD:
        return redirect(url_for('menu'))
    else:
        return redirect(url_for('index'))

@app.route('/menu')
def menu():
    return render_template('menu.html')

if __name__ == '__main__':
    app.run(debug=True)
