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
        return check_password_hash(self.password, password)

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
        
        # Generar el hash de la contraseña
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Crear el usuario y guardarlo en la base de datos
        new_user = User(id=None, username=username, email=email, password=hashed_password)
        new_user.save()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Obtener el usuario desde la base de datos usando la clase User
        user = User.get_by_username(username)
        
        if user and user.check_password(password):  # Verifica la contraseña con el hash
            # Actualiza el valor de admin a 1
            actualizar_admin(username)
            return redirect(url_for('index'))
        else:
            return redirect(url_for('register_admin'))  # Redirige si las credenciales son incorrectas
    # Si es una solicitud GET, muestra el formulario de inicio de sesión
    return render_template('register_admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"Username recibido: {username}")
        print(f"Password recibido: {password}")
        
        # Obtener el usuario desde la base de datos
        user = User.get_by_username(username)
        
        if user:
            print(f"Hash almacenado: {user.password}")
            print(f"Contraseña ingresada: {password}")
            if user.check_password(password):  # Verifica el hash de la contraseña
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
    # Obtener las propiedades que el usuario actual ha registrado
    cur = db.cursor()
    cur.execute("""
        SELECT p.direccion, p.comuna, u.username
        FROM system_tabla_propiedades p
        JOIN usuarios u ON p.id_usuario = u.id
        WHERE p.id_usuario = %s
    """, (current_user.id,))
    propiedades = cur.fetchall()
    cur.close()
    
    return render_template('portal_propiedad.html', propiedades=propiedades)


@app.route('/crear_empresa', methods=['POST'])
@login_required  # Solo usuarios autenticados pueden crear empresas
def crear_empresa():
    nombre_empresa = request.form['nombre_empresa']
    
    # Generar un código único para la empresa
    codigo_empresa = Generacion_Codigo_Unico()
    
    # Obtener el id del usuario autenticado
    id_usuario = current_user.id
    
    # Insertar la empresa en la base de datos y asociarla con el id del usuario
    cur = db.cursor()
    cur.execute("INSERT INTO empresas (codigo_empresa, nombre_empresa, id_usuario) VALUES (%s, %s, %s)", 
                (codigo_empresa, nombre_empresa, id_usuario))
    db.commit()
    cur.close()
    
    # No se muestra en el HTML inmediatamente, se redirige a la página de empresas
    return redirect(url_for('empresas'))

"""
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
"""
@app.route('/anadir_empresa', methods=['POST'])
@login_required
def anadir_empresa():
    codigo_empresa = request.form['codigo_empresa']
    
    # Verifica si la empresa con ese código pertenece al usuario autenticado
    cur = db.cursor()
    cur.execute("""
        SELECT codigo_empresa, nombre_empresa 
        FROM empresas 
        WHERE codigo_empresa = %s AND id_usuario = %s AND confirmada = False
    """, (codigo_empresa, current_user.id))
    empresa = cur.fetchone()
    
    if empresa:
        # Actualiza la columna 'confirmada' para mostrar la empresa en el HTML
        cur.execute("UPDATE empresas SET confirmada = True WHERE codigo_empresa = %s", (codigo_empresa,))
        db.commit()
        cur.close()
        
        # Redirigir a la página de empresas mostrando la empresa
        return redirect(url_for('empresas', nombre_empresa=empresa[1]))
    
    cur.close()
    # Si no se encuentra la empresa, redirigir sin cambios
    return redirect(url_for('empresas'))

"""
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
"""
@app.route('/empresas')
@login_required
def empresas():
    # Obtener solo las empresas confirmadas que están asociadas con el usuario autenticado
    cur = db.cursor()
    cur.execute("""
        SELECT codigo_empresa, nombre_empresa, 'Empleado', '24/10/2019' 
        FROM empresas 
        WHERE id_usuario = %s AND confirmada = True
    """, (current_user.id,))
    empresas = cur.fetchall()
    cur.close()
    
    # Crear una lista de diccionarios para pasarla al template
    empresas_lista = [{
        'nombre': empresa[1], 
        'logo': 'https://via.placeholder.com/110x110',
        'cargo': empresa[2],  
        'fecha_ingreso': empresa[3]
    } for empresa in empresas]
    
    return render_template('empresas.html', empresas=empresas_lista)

"""
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
"""

@app.route('/vista_propiedad')
def vista_propiedad():
    # Obtener las propiedades junto con el nombre del usuario que las registró
    cur = db.cursor()
    cur.execute("""
        SELECT p.id_propiedad, p.direccion, p.comuna, u.username, p.modificaciones
        FROM system_tabla_propiedades p
        JOIN usuarios u ON p.id_usuario = u.id
    """)
    propiedades = cur.fetchall()
    cur.close()
    
    return render_template('vista_propiedad.html', propiedades=propiedades)



@app.route('/registrar_propiedad', methods=['POST'])
@login_required  # Solo permitir a usuarios autenticados registrar propiedades
def registrar_propiedad():
    direccion = request.form['direccion']
    comuna = request.form['comuna']
    
    # Obtener el id del usuario de la sesión actual
    id_usuario = current_user.id
    
    # Insertar los datos en la tabla system_tabla_propiedades
    cur = db.cursor()
    cur.execute("INSERT INTO system_tabla_propiedades (direccion, comuna, id_usuario, modificaciones) VALUES (%s, %s, %s, %s)",
                (direccion, comuna, id_usuario, ""))
    db.commit()
    cur.close()
    
    return redirect(url_for('vista_propiedad'))

if __name__ == '__main__':
    app.run(debug=True)
