from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pytz import timezone, utc
import MySQLdb
import re
import random
import string
import requests


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
                    return redirect(url_for('empresas'))
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

@app.route('/crear_empresa', methods=['POST'])
@login_required
def crear_empresa():
    nombre_empresa = request.form['nombre_empresa']
    
    # Genera un código único para la empresa
    codigo_empresa = Generacion_Codigo_Unico()
    
    # Inserta la empresa en la base de datos con el usuario como creador
    cur = db.cursor()
    cur.execute("INSERT INTO empresas (codigo_empresa, nombre_empresa, id_usuario) VALUES (%s, %s, %s)", 
                (codigo_empresa, nombre_empresa, current_user.id))
    
    # Añadir al creador como miembro de su propia empresa
    cur.execute("INSERT INTO usuarios_empresas (id_usuario, codigo_empresa) VALUES (%s, %s)", 
                (current_user.id, codigo_empresa))
    db.commit()
    cur.close()
    
    # Redirige de vuelta a la página de empresas
    return redirect(url_for('empresas'))

@app.route('/anadir_empresa', methods=['POST'])
@login_required
def anadir_empresa():
    codigo_empresa = request.form['codigo_empresa']
    
    # Verifica si el código de la empresa existe
    cur = db.cursor()
    cur.execute("SELECT codigo_empresa FROM empresas WHERE codigo_empresa = %s", (codigo_empresa,))
    empresa = cur.fetchone()
    
    if empresa:
        # Añadir al usuario a la empresa
        cur.execute("INSERT INTO usuarios_empresas (id_usuario, codigo_empresa) VALUES (%s, %s)", 
                    (current_user.id, codigo_empresa))
        db.commit()
        cur.close()
        
        # Redirige a la página de empresas
        return redirect(url_for('empresas'))
    
    cur.close()
    # Si no se encuentra la empresa, redirigir sin cambios
    return redirect(url_for('empresas'))

@app.route('/empresas')
@login_required
def empresas():
    # Obtener las empresas en las que el usuario es miembro
    cur = db.cursor()
    cur.execute("""
        SELECT e.codigo_empresa, e.nombre_empresa, 'Empleado', '24/10/2019'
        FROM empresas e
        INNER JOIN usuarios_empresas ue ON e.codigo_empresa = ue.codigo_empresa
        WHERE ue.id_usuario = %s
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

@app.route('/registrar_propiedad', methods=['POST'])
@login_required
def registrar_propiedad():
    direccion = request.form['direccion']
    comuna = request.form['comuna']
    id_usuario = current_user.id
    
    # Obtener el código de empresa del usuario desde la tabla usuarios_empresas
    cur = db.cursor()
    cur.execute("""
        SELECT codigo_empresa FROM usuarios_empresas 
        WHERE id_usuario = %s
    """, (id_usuario,))
    codigo_empresa = cur.fetchone()
    
    if not codigo_empresa:
        return "No puedes registrar una propiedad porque no perteneces a ninguna empresa.", 403

    # Verificar si ya existe una propiedad con la misma dirección y comuna
    cur.execute("""
        SELECT COUNT(*) FROM system_tabla_propiedades
        WHERE direccion = %s AND comuna = %s
    """, (direccion, comuna))
    propiedad_existente = cur.fetchone()[0]
    
    if propiedad_existente > 0:
        # Propiedad duplicada, devolver un mensaje de advertencia
        return "Ya existe una propiedad con la misma dirección y comuna.", 409  # Código 409: Conflicto

    # Insertar la propiedad
    cur.execute("""
        INSERT INTO system_tabla_propiedades (direccion, comuna, id_usuario, modificaciones, codigo_empresa) 
        VALUES (%s, %s, %s, %s, %s)
    """, (direccion, comuna, id_usuario, "", codigo_empresa))
    db.commit()
    cur.close()
    
    return redirect(url_for('vista_propiedad'))

@app.route('/vista_propiedad')
@login_required
def vista_propiedad():
    id_usuario = current_user.id
    
    # Verificar el código de empresa del usuario en la tabla usuarios_empresas
    cur = db.cursor()
    cur.execute("""
        SELECT codigo_empresa FROM usuarios_empresas 
        WHERE id_usuario = %s
    """, (id_usuario,))
    codigo_empresa = cur.fetchone()
    
    if not codigo_empresa:
        return "No perteneces a ninguna empresa.", 403

    # Obtener las propiedades relacionadas con esa empresa
    cur.execute("""
        SELECT p.id_propiedad, p.direccion, p.comuna, p.modificaciones, u.username 
        FROM system_tabla_propiedades p
        JOIN usuarios u ON p.id_usuario = u.id
        WHERE p.codigo_empresa = %s
    """, (codigo_empresa,))
    propiedades = cur.fetchall()
    cur.close()
    
    return render_template('vista_propiedad.html', propiedades=propiedades)

@app.route('/portal_propiedad/<int:id_propiedad>')
@login_required
def portal_propiedad(id_propiedad):
    # Obtener la propiedad seleccionada por el id_propiedad
    cur = db.cursor()
    cur.execute("""
        SELECT p.id_propiedad, p.direccion, p.comuna, u.username
        FROM system_tabla_propiedades p
        JOIN usuarios u ON p.id_usuario = u.id
        WHERE p.id_propiedad = %s
    """, (id_propiedad,))
    propiedad = cur.fetchone()
    cur.close()

    if not propiedad:
        return "Propiedad no encontrada", 404

    # Pasar la propiedad seleccionada al template
    return render_template('portal_propiedad.html', propiedad=propiedad, es_admin=current_user.is_admin)

@app.route('/editar_propiedad/<int:propiedad_id>', methods=['POST'])
@login_required
def editar_propiedad(propiedad_id):
    direccion = request.form['direccion']
    comuna = request.form['comuna']

    # Actualizar la propiedad en la base de datos
    cur = db.cursor()
    cur.execute("""
        UPDATE system_tabla_propiedades
        SET direccion = %s, comuna = %s
        WHERE id_propiedad = %s
    """, (direccion, comuna, propiedad_id))
    db.commit()
    cur.close()

    return redirect(url_for('portal_propiedad', id_propiedad=propiedad_id))

@app.route('/eliminar_propiedad/<int:propiedad_id>', methods=['POST'])
@login_required
def eliminar_propiedad(propiedad_id):
    # Verificar que la propiedad le pertenece al usuario autenticado o que es accesible
    cur = db.cursor()
    cur.execute("""
        DELETE FROM system_tabla_propiedades 
        WHERE id_propiedad = %s
    """, (propiedad_id,))
    
    db.commit()
    cur.close()

    return redirect(url_for('vista_propiedad'))

# Función para obtener el access token usando client_id y client_secret

def obtener_access_token():
    zoom_token_url = "https://zoom.us/oauth/token"
    client_id = "ggJgqtaDSzyijA32f7GlBg"
    client_secret = "5nSNBkaHTBEt3ty17rW6S9tb5wgOqXxD"
    account_id = 'HjvAH6DfSd--ZpzDUZW_qw'

    # Cabeceras para la autenticación
    auth = (client_id, client_secret)
    
    data = {
        'grant_type': 'account_credentials',
        'account_id': account_id
    }

    # Hacer la solicitud para obtener el token de acceso
    response = requests.post(zoom_token_url, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, auth=auth, data=data)
    
    # Imprimir la respuesta para depurar
    print("Estado de respuesta:", response.status_code)
    print("Contenido de la respuesta:", response.json())

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Error al obtener el token de acceso: {response.status_code}, {response.text}")

# Crear el filtro personalizado
@app.template_filter('tolocal')
def tolocal(utc_time_str):
    # Asumiendo que la fecha viene en formato ISO 8601 (2024-10-03T21:50:00Z)
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    
    # Convertir UTC a la zona horaria de Chile (America/Santiago)
    local_tz = timezone('America/Santiago')
    local_time = utc_time.replace(tzinfo=utc).astimezone(local_tz)
    
    # Formatear la fecha y hora a un formato legible
    return local_time.strftime('%Y-%m-%d %H:%M')

zoom_token_url = "https://zoom.us/oauth/token"
zoom_meeting_url = "https://api.zoom.us/v2/users/me/meetings"
    
@app.route('/crear_reunion/<int:propiedad_id>', methods=['POST'])
@login_required
def crear_reunion(propiedad_id):
    # Obtener la fecha y hora seleccionadas desde el formulario
    fecha_hora_seleccionada = request.form.get('fecha_hora')  # Esto viene del campo oculto en el formulario
    
    print(f"Fecha y hora seleccionadas: {fecha_hora_seleccionada}")  # Verificar el valor recibido

    if not fecha_hora_seleccionada:
        return "Debe seleccionar una fecha y hora para la reunión.", 400

    # Verificar si el usuario tiene acceso a la propiedad
    cur = db.cursor()
    cur.execute("""
        SELECT id_usuario FROM system_tabla_propiedades
        WHERE id_propiedad = %s
    """, (propiedad_id,))
    propiedad = cur.fetchone()

    if not propiedad or propiedad[0] != current_user.id:
        return "No tienes permiso para crear una reunión para esta propiedad.", 403

    # Obtener el token de acceso de Zoom
    access_token = obtener_access_token()

    # Configuración de la reunión
    meeting_data = {
        "topic": "Reunión para propiedad",
        "type": 2,  # Reunión programada
        "start_time": fecha_hora_seleccionada,  # Usar la fecha y hora seleccionadas por el usuario
        "duration": 40,  # Reunión de 40 minutos
        "timezone": "America/Santiago",
        "agenda": f"Reunión para discutir la propiedad ID {propiedad_id}",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": False,
            "mute_upon_entry": True,
            "approval_type": 1,  # Aprobación automática
            "audio": "voip"
        }
    }

    # Hacer la solicitud a Zoom para crear la reunión
    response = requests.post(zoom_meeting_url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }, json=meeting_data)

    if response.status_code == 201:
        meeting_info = response.json()
        join_url = meeting_info['join_url']
        topic = meeting_info['topic']
        start_time = meeting_info['start_time']
        duration = meeting_info['duration']
        agenda = meeting_info.get('agenda', "Sin agenda")

        # Redirigir a la página invite.html con los detalles de la reunión
        return redirect(url_for('invite', join_url=join_url, topic=topic, start_time=start_time, duration=duration, agenda=agenda))
    else:
        return f"Error al crear la reunión: {response.status_code}", response.text



@app.route('/invite')
@login_required
def invite():
    join_url = request.args.get('join_url')
    topic = request.args.get('topic')
    start_time = request.args.get('start_time')
    duration = request.args.get('duration')
    agenda = request.args.get('agenda')

    # Verificar si join_url fue proporcionado
    if not join_url:
        return "No se encontró el enlace de la reunión.", 400

    # Obtener el id del usuario actual (administrador)
    admin_id = current_user.id

    # Consultar el código de empresa del administrador
    cur = db.cursor()
    cur.execute("""
        SELECT codigo_empresa 
        FROM usuarios_empresas 
        WHERE id_usuario = %s
    """, (admin_id,))
    codigo_empresa = cur.fetchone()

    if not codigo_empresa:
        return "No se pudo obtener el código de empresa del administrador.", 403

    # Obtener todos los usuarios que pertenecen a la misma empresa (mismo codigo_empresa)
    cur.execute("""
        SELECT u.id, u.username, u.email 
        FROM usuarios u
        JOIN usuarios_empresas ue ON u.id = ue.id_usuario
        WHERE ue.codigo_empresa = %s
    """, (codigo_empresa[0],))
    usuarios = cur.fetchall()
    cur.close()

    # Renderizar el template 'invite.html' pasando los detalles de la reunión y la lista de usuarios
    return render_template('invite.html', usuarios=usuarios, join_url=join_url, topic=topic, start_time=start_time, duration=duration, agenda=agenda)

@app.route('/enviar_invitaciones', methods=['POST'])
@login_required
def enviar_invitaciones():
    # Recibir correos seleccionados
    correos = request.form.getlist('usuarios')
    join_url = request.form['join_url']
    
    cur = db.cursor()

    # Por cada correo seleccionado, buscamos al usuario y le creamos una notificación
    for correo in correos:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (correo,))
        usuario = cur.fetchone()
        
        if usuario:
            id_usuario = usuario[0]
            mensaje = f"Has sido invitado a una reunión. Únete usando este enlace: {join_url}"
            
            # Guardar notificación en la base de datos
            cur.execute("""
                INSERT INTO notificaciones (id_usuario, mensaje) 
                VALUES (%s, %s)
            """, (id_usuario, mensaje))
    
    db.commit()
    cur.close()

    return f"Notificaciones enviadas a los usuarios seleccionados."

@app.route('/notificaciones')
@login_required
def notificaciones():
    cur = db.cursor()
    
    # Obtener las notificaciones no leídas para el usuario actual
    cur.execute("""
        SELECT id, mensaje, fecha FROM notificaciones 
        WHERE id_usuario = %s AND leido = FALSE
        ORDER BY fecha DESC
    """, (current_user.id,))
    
    notificaciones = cur.fetchall()
    cur.close()
    
    return render_template('notificaciones.html', notificaciones=notificaciones)

@app.route('/marcar_leido/<int:id>', methods=['POST'])
@login_required
def marcar_leido(id):
    cur = db.cursor()

    # Marcar la notificación como leída
    cur.execute("""
        UPDATE notificaciones
        SET leido = TRUE
        WHERE id = %s AND id_usuario = %s
    """, (id, current_user.id))
    
    db.commit()
    cur.close()

    return redirect(url_for('notificaciones'))


if __name__ == '__main__':
    app.run(debug=True)