from flask import Flask, render_template, request, redirect, url_for
import random
import string
import MySQLdb
import re

app = Flask(__name__)

# Configurar la conexión a la base de datos
db = MySQLdb.connect(
    host="autorack.proxy.rlwy.net",    # Host proporcionado por Railway
    user="root",                       # Usuario proporcionado por Railway
    passwd="fzRHqqgyogtYsSpkOqpjBpcfqIowFdzg",  # Contraseña proporcionada por Railway
    db="railway",                      # Nombre de la base de datos proporcionado por Railway
    port=15660                         # Puerto proporcionado por Railway
)

def Generacion_Codigo_Unico(length=20):
    caracteres = string.ascii_letters + string.digits
    codigo_unico = ''.join(random.choice(caracteres) for _ in range(length))
    return codigo_unico

# Función para verificar credenciales de usuario
def verificar_usuario(username, password):
    cur = db.cursor()
    cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
    usuario = cur.fetchone()  # Devuelve el primer resultado o None si no existe
    cur.close()
    return usuario

def actualizar_admin(username):
    cur = db.cursor()
    cur.execute("UPDATE usuarios SET admin = 1 WHERE username = %s", (username,))
    db.commit()
    cur.close()

def agregar_usuario(username, email, password):
    cur = db.cursor()
    # Inserta al usuario con admin=1 por defecto
    cur.execute("INSERT INTO usuarios (username, email, password, admin) VALUES (%s, %s, %s, %s)", 
                (username, email, password, 0))
    db.commit()
    cur.close()    


@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validación básica
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Dirección de correo no válida"
        if password != confirm_password:
            return "Las contraseñas no coinciden"
        
        # Verificar si el usuario o email ya existe
        cur = db.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username = %s OR email = %s", (username, email))
        usuario = cur.fetchone()
        if usuario:
            return "El usuario o email ya están registrados"
        
        # Agregar el usuario a la base de datos
        agregar_usuario(username, email, password)
        return redirect(url_for('login'))  # Redirigir al login después del registro
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        usuario = verificar_usuario(username, password)
        
        if usuario:
            # `usuario[3]` asume que `admin` es la cuarta columna devuelta en el resultado.
            # Asegúrate de que el orden de las columnas en tu tabla coincida.
            if usuario[4] == 1:  # Si el usuario es admin
                return redirect(url_for('duality'))
            else:
                return redirect(url_for('portal_propiedad'))
        else:
            return redirect(url_for('index'))
    # Si es una solicitud GET, muestra el formulario de inicio de sesión
    return render_template('index.html')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        usuario = verificar_usuario(username, password)
        
        if usuario:
            # Actualiza el valor de admin a 1
            actualizar_admin(username)
            return redirect(url_for('index'))
        else:
            return redirect(url_for('register_admin'))
    # Si es una solicitud GET, muestra el formulario de inicio de sesión
    return render_template('register_admin.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/duality')
def duality():
    return render_template('duality.html')

@app.route('/empresas')
def empresas():
    return render_template('empresas.html')

@app.route('/crear_empresa', methods=['POST'])
def crear_empresa():
    nombre_empresa = request.form['nombre_empresa']
    
    # Genera un código único para la empresa
    codigo_empresa = Generacion_Codigo_Unico()
    
    # Inserta el nombre de la empresa y el código único en la base de datos
    cur = db.cursor()
    cur.execute("INSERT INTO empresas (codigo_empresa, nombre_empresa) VALUES (%s, %s)", (codigo_empresa, nombre_empresa))
    db.commit()
    cur.close()
    
    # Redirige de vuelta a la página de empresas
    return redirect(url_for('empresas'))



@app.route('/vista_propiedad')
def vista_propiedad():
    return render_template('vista_propiedad.html')

@app.route('/portal_propiedad')
def portal_propiedad():
    return render_template('portal_propiedad.html')

if __name__ == '__main__':
    app.run(debug=True)
