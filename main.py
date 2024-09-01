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
    
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/duality')
def duality():
    return render_template('duality.html')

@app.route('/empresas')
def empresas():
    return render_template('empresas.html')

if __name__ == '__main__':
    app.run(debug=True)
