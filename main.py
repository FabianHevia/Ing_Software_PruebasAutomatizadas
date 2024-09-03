from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import re
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para manejar sesiones

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
"""
# Función para verificar credenciales de usuario
def verificar_usuario(username, password):
    cur = db.cursor()
    cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
    usuario = cur.fetchone()  # Devuelve el primer resultado o None si no existe
    cur.close()
    return usuario
"""

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
# Inicializar LoginManager para manejar autenticaciones
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email, password, is_admin=False, empresa=False):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.empresa = empresa  # Añadimos empresa al constructor

    def check_password(self, password):
        return self.password == password  # Compara directamente en texto plano

    @staticmethod
    def get_by_username(username):
        cur = db.cursor()
        cur.execute("SELECT id, username, email, password, admin, empresa FROM usuarios WHERE username = %s", (username,))
        user_data = cur.fetchone()
        cur.close()
        
        if user_data:
            return User(id=user_data[0], username=user_data[1], email=user_data[2], 
                        password=user_data[3], is_admin=bool(user_data[4]), empresa=bool(user_data[5]))
        return None

    @staticmethod
    def get_by_id(user_id):
        cur = db.cursor()
        cur.execute("SELECT id, username, email, password, admin, empresa FROM usuarios WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
        cur.close()

        if user_data:
            return User(id=user_data[0], username=user_data[1], email=user_data[2], 
                        password=user_data[3], is_admin=bool(user_data[4]), empresa=bool(user_data[5]))
        return None

    def save(self):
        cur = db.cursor()
        cur.execute("INSERT INTO usuarios (username, email, password, admin, empresa) VALUES (%s, %s, %s, %s, %s)", 
                    (self.username, self.email, self.password, int(self.is_admin), int(self.empresa)))
        db.commit()
        cur.close()



@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

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
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Dirección de correo no válida"
        if password != confirm_password:
            return "Las contraseñas no coinciden"
        
        if User.get_by_username(username):
            return "El usuario ya está registrado"
        
        # NO Generar el hash de la contraseña, solo almacenar el texto plano
        new_user = User(id=None, username=username, email=email, password=password)
        new_user.save()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.get_by_username(username)
        
        if user:
            print(f"Usuario encontrado: {user.username}, Contraseña en DB: {user.password}, Contraseña ingresada: {password}")
            if user.check_password(password):
                print("Contraseña correcta")
                login_user(user)
                if user.is_admin:
                    return redirect(url_for('duality'))
                else:
                    return redirect(url_for('portal_propiedad'))
            else:
                print("Contraseña incorrecta")
        else:
            print("Usuario no encontrado")
            
        return "Usuario o contraseña incorrectos"
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/duality')
@login_required
def duality():
    return render_template('duality.html')

@app.route('/portal_propiedad')
@login_required
def portal_propiedad():
    return render_template('portal_propiedad.html')


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

@app.route('/anadir_empresa', methods=['POST'])
def anadir_empresa():
    codigo_empresa = request.form['codigo_empresa']
    
    # Verifica si la empresa con ese código existe
    cur = db.cursor()
    cur.execute("SELECT nombre_empresa FROM empresas WHERE codigo_empresa = %s", (codigo_empresa,))
    empresa = cur.fetchone()
    
    cur.close()
    
    if empresa:
        # Si la empresa existe, agregar el nombre a la lista para mostrar en la tabla
        return redirect(url_for('empresas', nombre_empresa=empresa[0]))
    
    return redirect(url_for('empresas'))  # Si no se encuentra la empresa, redirige sin agregar

@app.route('/empresas')
def empresas():
    nombre_empresa = request.args.get('nombre_empresa')
    
    # Aquí podemos crear una lista de las empresas que se muestran en la tabla
    empresas = []
    
    if nombre_empresa:
        # Añadir la nueva empresa a la lista de empresas a mostrar
        empresas.append({
            'nombre': nombre_empresa,
            'logo': 'https://via.placeholder.com/110x110',
            'cargo': 'Empleado',
            'fecha_ingreso': '24/10/2019'
        })
    
    return render_template('empresas.html', empresas=empresas)



@app.route('/vista_propiedad')
def vista_propiedad():
    # Obtener las propiedades desde la base de datos
    cur = db.cursor()
    cur.execute("SELECT direccion, comuna, codigo_postal, url_imagen FROM propiedades")
    propiedades = cur.fetchall()
    cur.close()
    
    # Pasar las propiedades al template
    return render_template('vista_propiedad.html', propiedades=propiedades)


@app.route('/registrar_propiedad', methods=['POST'])
def registrar_propiedad():
    direccion = request.form['direccion']
    comuna = request.form['comuna']
    codigo_postal = request.form['codigo_postal']
    url_imagen = request.form['url_imagen']
    
    
    # Insertar los datos en la base de datos
    cur = db.cursor()
    cur.execute("INSERT INTO propiedades (direccion, comuna, codigo_postal, url_imagen) VALUES (%s, %s, %s, %s)",
                (direccion, comuna, codigo_postal, url_imagen))
    db.commit()
    cur.close()
    
    return redirect(url_for('vista_propiedad'))

if __name__ == '__main__':
    app.run(debug=True)
