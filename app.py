from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from pytz import timezone, utc
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from config import Config
from models import db, Empresa, Favorito, Notificacion, Propiedad, Usuario, UsuarioEmpresa, VisitaPropiedad, LogActividad, ComentarioPropiedad
import os
import re
import random
import string
import requests
import cloudinary
import cloudinary.uploader
import config

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para manejar sesiones
# Configurar la conexión a la base de datos con SQLAlchemy
app.config.from_object(Config)
# Inicializa la base de datos con la aplicación
db.init_app(app)

cloudinary.config(
    cloud_name='dzjp7l61z',
    api_key='678348253613332',
    api_secret='DJ_y5npwR2qkobe69hHtyGW8ZKU'
)

# Después de este paso, puedes comenzar a usar `db.session` para manejar las operaciones de base de datos en lugar de `cur` de `psycopg2`.
# Configuraciones para manejar las imágenes
UPLOAD_FOLDER = 'ruta/donde/guardar/imagenes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def Generacion_Codigo_Unico(length=20):
    caracteres = string.ascii_letters + string.digits
    codigo_unico = ''.join(random.choice(caracteres) for _ in range(length))
    return codigo_unico

def actualizar_admin(username):
    user = Usuario.query.filter_by(username=username).first()
    if user:
        user.admin = 1
        db.session.commit()

def agregar_usuario(username, email, password):
    new_user = Usuario(
        username=username,
        email=email,
        password=password,
        admin=0
    )
    db.session.add(new_user)
    db.session.commit()  
# Inicializar LoginManager para manejar autenticaciones
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.get_by_id(user_id)

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
            flash("Dirección de correo no válida")
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('register'))
        
        # Verificar si el usuario ya existe
        existing_user = Usuario.query.filter_by(username=username).first()
        if existing_user:
            flash("El usuario ya está registrado")
            return redirect(url_for('register'))
        
        # Crear el usuario y guardarlo en la base de datos
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        print(f"Hash generado: {hashed_password}")
        new_user = Usuario(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registro exitoso, puedes iniciar sesión")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Obtener el usuario desde la base de datos usando el modelo Usuario
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):  # Verifica la contraseña con el hash
            # Actualiza el valor de admin a 1
            user.admin = 1
            db.session.commit()
            return redirect(url_for('index'))
        else:
            flash("Credenciales incorrectas")
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
        user = Usuario.query.filter_by(username=username).first()
        
        if user:
            print(f"Hash almacenado en la base de datos: {user.password}")
            print(f"Contraseña ingresada: {password}")
            if user and check_password_hash(user.password, password):
                print("Contraseña correcta")
                login_user(user)
                if user.admin or user.acceso_crm:  # acceso_crm es el campo de permiso
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
    
    # Crea una nueva instancia de Empresa y la agrega a la sesión
    nueva_empresa = Empresa(
        codigo_empresa=codigo_empresa, 
        nombre_empresa=nombre_empresa, 
        id_usuario=current_user.id
    )
    db.session.add(nueva_empresa)
    
    # Crea una instancia en la tabla de relación UsuarioEmpresa para el creador
    usuario_empresa = UsuarioEmpresa(
        id_usuario=current_user.id, 
        codigo_empresa=codigo_empresa
    )
    db.session.add(usuario_empresa)
    
    # Guarda los cambios en la base de datos
    db.session.commit()
    
    # Redirige de vuelta a la página de empresas
    return redirect(url_for('empresas'))

@app.route('/anadir_empresa', methods=['POST'])
@login_required
def anadir_empresa():
    codigo_empresa = request.form['codigo_empresa']
    
    # Verifica si el código de la empresa existe
    empresa = Empresa.query.filter_by(codigo_empresa=codigo_empresa).first()
    
    if empresa:
        # Añadir al usuario a la empresa
        usuario_empresa = UsuarioEmpresa(
            id_usuario=current_user.id, 
            codigo_empresa=codigo_empresa
        )
        db.session.add(usuario_empresa)
        db.session.commit()
        
        # Redirige a la página de empresas
        return redirect(url_for('empresas'))
    
    # Si no se encuentra la empresa, redirigir sin cambios
    return redirect(url_for('empresas'))

@app.route('/empresas')
@login_required
def empresas():
    # Obtener las empresas en las que el usuario es miembro
    empresas_usuario = (
        db.session.query(Empresa.codigo_empresa, Empresa.nombre_empresa)
        .join(UsuarioEmpresa, Empresa.codigo_empresa == UsuarioEmpresa.codigo_empresa)
        .filter(UsuarioEmpresa.id_usuario == current_user.id)
        .all()
    )

    # Crear una lista de diccionarios para pasarla al template
    empresas_lista = [{
        'nombre': empresa[1], 
        'logo': 'https://via.placeholder.com/110x110',
        'cargo': 'Empleado',
        'fecha_ingreso': '24/10/2019'  # Puede ajustarse si tienes una fecha real
    } for empresa in empresas_usuario]
    
    return render_template('empresas.html', empresas=empresas_lista)

@app.route('/registrar_propiedad', methods=['POST'])
@login_required
def registrar_propiedad():
    direccion = request.form['direccion']
    comuna = request.form['comuna']
    imagen = request.files['imagen']  # Obtener la imagen del formulario

    # Verificar si se subió la imagen
    if imagen:
        # Subir la imagen a Cloudinary
        result = cloudinary.uploader.upload(imagen)
        imagen_url = result['secure_url']  # Obtener la URL segura de la imagen subida
    else:
        imagen_url = None  # Si no se sube imagen, dejar el campo vacío o usar una predeterminada

    # Obtener el código de empresa del usuario desde la tabla usuarios_empresas
    empresa_usuario = UsuarioEmpresa.query.filter_by(id_usuario=current_user.id).first()
    
    if not empresa_usuario:
        return "No puedes registrar una propiedad porque no perteneces a ninguna empresa.", 403

    # Verificar si ya existe una propiedad con la misma dirección y comuna
    propiedad_existente = Propiedad.query.filter_by(direccion=direccion, comuna=comuna).count()
    
    if propiedad_existente > 0:
        # Propiedad duplicada, devolver un mensaje de advertencia
        return "Ya existe una propiedad con la misma dirección y comuna.", 409  # Código 409: Conflicto

    # Crear e insertar la nueva propiedad
    nueva_propiedad = Propiedad(
        direccion=direccion,
        comuna=comuna,
        id_usuario=current_user.id,
        modificaciones="",
        codigo_empresa=empresa_usuario.codigo_empresa,
        imagen=imagen_url
    )

    db.session.add(nueva_propiedad)
    
    # Registrar la acción del usuario en la tabla de actividades
    log_actividad = LogActividad(
        id_usuario=current_user.id,
        codigo_empresa=empresa_usuario.codigo_empresa,
        accion="Registrar propiedad",
        detalle=f"Propiedad en {direccion}, {comuna} registrada"
    )
    db.session.add(log_actividad)
    db.session.commit()
    
    return redirect(url_for('vista_propiedad'))

@app.route('/vista_propiedad')
@login_required
def vista_propiedad():
    # Verificar el código de empresa del usuario en la tabla usuarios_empresas
    empresa_usuario = UsuarioEmpresa.query.filter_by(id_usuario=current_user.id).first()
    
    if not empresa_usuario:
        return "No perteneces a ninguna empresa.", 403

    # Obtener las propiedades relacionadas con esa empresa, incluyendo la URL de la imagen y el nombre del usuario
    propiedades = (
        db.session.query(Propiedad, Usuario.username)
        .join(Usuario, Propiedad.id_usuario == Usuario.id)
        .filter(Propiedad.codigo_empresa == empresa_usuario.codigo_empresa)
        .order_by(Propiedad.id_propiedad.asc())
        .all()
    )

    # Procesar la lista para renderizarla correctamente en la plantilla
    propiedades_lista = [
        {
            'id_propiedad': propiedad.id_propiedad,
            'direccion': propiedad.direccion,
            'comuna': propiedad.comuna,
            'modificaciones': propiedad.modificaciones,
            'username': username,
            'imagen': propiedad.imagen
        }
        for propiedad, username in propiedades
    ]
    
    return render_template('vista_propiedad.html', propiedades=propiedades_lista)

@app.route('/portal_propiedad/<int:id_propiedad>')
@login_required
def portal_propiedad(id_propiedad):
    # Verificar si ya existe una visita para este usuario y propiedad
    visita_existente = VisitaPropiedad.query.filter_by(id_propiedad=id_propiedad, id_usuario=current_user.id).count()

    # Solo insertar la visita si no existe
    if visita_existente == 0:
        nueva_visita = VisitaPropiedad(id_propiedad=id_propiedad, id_usuario=current_user.id, fecha_visita=datetime.now())
        db.session.add(nueva_visita)
        db.session.commit()

    # Obtener la propiedad y el total de visitas
    propiedad = (
        db.session.query(Propiedad, Usuario.username, Usuario.id.label("id_usuario"))
        .join(Usuario, Propiedad.id_usuario == Usuario.id)
        .filter(Propiedad.id_propiedad == id_propiedad)
        .first()
    )
    
    # Total de visitas a la propiedad
    total_visitas = VisitaPropiedad.query.filter_by(id_propiedad=id_propiedad).count()

    # Verificar si la propiedad es favorita
    es_favorito = Favorito.query.filter_by(id_usuario=current_user.id, id_propiedad=id_propiedad).first() is not None

    # Obtener solo los comentarios principales (sin padre)
    comentarios = ComentarioPropiedad.query.filter_by(id_propiedad=id_propiedad, id_comentario_padre=None).all()

    # Preparar los datos para la plantilla
    propiedad_data = {
        'id_propiedad': propiedad.Propiedad.id_propiedad,
        'direccion': propiedad.Propiedad.direccion,
        'comuna': propiedad.Propiedad.comuna,
        'username': propiedad.username,
        'id_usuario': propiedad.id_usuario,
        'imagen': propiedad.Propiedad.imagen
    }
    
    return render_template(
        'portal_propiedad.html', 
        propiedad=propiedad_data, 
        es_favorito=es_favorito, 
        es_admin=current_user.is_admin, 
        total_visitas=total_visitas,
        comentarios=comentarios  # Pasar los comentarios al template
    )
    
@app.route('/editar_propiedad/<int:propiedad_id>', methods=['POST'])
@login_required
def editar_propiedad(propiedad_id):
    direccion = request.form['direccion']
    comuna = request.form['comuna']

    # Actualizar la propiedad en la base de datos
    propiedad = Propiedad.query.get(propiedad_id)
    if propiedad:
        propiedad.direccion = direccion
        propiedad.comuna = comuna
        db.session.commit()

        # Crear mensaje de notificación
        mensaje = f"La propiedad {propiedad_id} en {direccion}, {comuna} ha sido actualizada."

        # Obtener los usuarios que tienen la propiedad en favoritos
        usuarios_favoritos = Favorito.query.filter_by(id_propiedad=propiedad_id).all()
        
        # Obtener el código de empresa del usuario desde la tabla usuarios_empresas
        empresa_usuario = UsuarioEmpresa.query.filter_by(id_usuario=current_user.id).first()

        # Enviar notificación a cada usuario con el campo `leido` como no leído (0)
        for usuario in usuarios_favoritos:
            notificacion = Notificacion(id_usuario=usuario.id_usuario, mensaje=mensaje, leido=0)
            db.session.add(notificacion)

        # Añadir el registro al Log de Actividad
        accion = f"Edición de propiedad"
        detalle = f"Propiedad {propiedad_id} en {direccion}, {comuna} actualizada por el usuario {current_user.username}."
        log_actividad = LogActividad(
            id_usuario=current_user.id,
            codigo_empresa=empresa_usuario.codigo_empresa, 
            accion=accion,
            detalle=detalle,
            fecha_hora=datetime.utcnow()
        )
        db.session.add(log_actividad)
        
        db.session.commit()
        flash("La propiedad ha sido actualizada y se ha notificado a los usuarios correspondientes.")
    else:
        flash("La propiedad no fue encontrada.")

    return redirect(url_for('portal_propiedad', id_propiedad=propiedad_id))

@app.route('/eliminar_propiedad/<int:propiedad_id>', methods=['POST'])
@login_required
def eliminar_propiedad(propiedad_id):
    
    # Eliminar los favoritos asociados a la propiedad
    favoritos = Favorito.query.filter_by(id_propiedad=propiedad_id).all()
    for favorito in favoritos:
        db.session.delete(favorito)
    # Eliminar las visitas asociadas a la propiedad
    visitas = VisitaPropiedad.query.filter_by(id_propiedad=propiedad_id).all()
    for visita in visitas:
        db.session.delete(visita)
    # Obtener el código de empresa del usuario desde la tabla usuarios_empresas
    empresa_usuario = UsuarioEmpresa.query.filter_by(id_usuario=current_user.id).first()
    # Eliminar la propiedad
    propiedad = Propiedad.query.get(propiedad_id)
    if propiedad:
        db.session.delete(propiedad)
        db.session.commit()
        # Registrar la acción en el Log de Actividad
        accion = "Eliminación de propiedad"
        detalle = f"Propiedad {propiedad_id} eliminada por el usuario {current_user.username}."
        log_actividad = LogActividad(
            id_usuario=current_user.id,
            codigo_empresa=empresa_usuario.codigo_empresa, 
            accion=accion,
            detalle=detalle,
            fecha_hora=datetime.utcnow()
        )
        db.session.add(log_actividad)
        db.session.commit()
        flash("Propiedad eliminada correctamente.")
    else:
        flash("La propiedad no fue encontrada.")

    return redirect(url_for('vista_propiedad'))

@app.route('/agregar_favorito', methods=['POST'])
@login_required
def agregar_favorito():
    data = request.get_json()
    id_propiedad = data.get('id_propiedad')

    # Verificar si la propiedad ya está en favoritos
    favorito_existente = Favorito.query.filter_by(id_usuario=current_user.id, id_propiedad=id_propiedad).first()

    if favorito_existente:
        return jsonify(success=False, message="La propiedad ya está en favoritos."), 400

    # Agregar la propiedad a la tabla de favoritos
    nuevo_favorito = Favorito(id_usuario=current_user.id, id_propiedad=id_propiedad)
    db.session.add(nuevo_favorito)
    db.session.commit()

    return jsonify(success=True, message="Propiedad agregada a favoritos.")

@app.route('/quitar_favorito', methods=['DELETE'])
@login_required
def quitar_favorito():
    data = request.get_json()
    id_propiedad = data.get('id_propiedad')

    # Buscar y eliminar el favorito en la base de datos
    favorito = Favorito.query.filter_by(id_usuario=current_user.id, id_propiedad=id_propiedad).first()

    if favorito:
        db.session.delete(favorito)
        db.session.commit()
        return jsonify(success=True, message="Propiedad eliminada de favoritos.")
    else:
        return jsonify(success=False, message="La propiedad no se encuentra en favoritos."), 404

@app.route('/favoritos')
@login_required
def favoritos():
    # Obtener las propiedades favoritas del usuario actual
    favoritos = (
        db.session.query(Propiedad.id_propiedad, Propiedad.direccion, Propiedad.comuna)
        .join(Favorito, Favorito.id_propiedad == Propiedad.id_propiedad)
        .filter(Favorito.id_usuario == current_user.id)
        .all()
    )

    # Renderizar la plantilla favoritos.html pasando los favoritos
    return render_template('favoritos.html', favoritos=favoritos)

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
    
# Crear el filtro de hora personalizado
@app.template_filter('tolocal')
def tolocal(utc_time_str):
    try:
        # Intentar con el formato ISO 8601
        utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        try:
            # Intentar un formato alternativo si es necesario
            utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return "Formato de fecha no válido"
    
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
    fecha_hora_seleccionada = request.form.get('fecha_hora')
    
    if not fecha_hora_seleccionada:
        return "Debe seleccionar una fecha y hora para la reunión.", 400

    # Verificar si el usuario tiene acceso a la propiedad
    propiedad = Propiedad.query.get(propiedad_id)
    if not propiedad:
        return "Propiedad no encontrada.", 404

    # Si no es administrador, ni tiene el permiso de crear reuniones, verificar que sea el dueño de la propiedad
    if not (current_user.is_admin or current_user.crear_reuniones or propiedad.id_usuario == current_user.id):
        return "No tienes permiso para crear una reunión para esta propiedad.", 403

    # Obtener el token de acceso de Zoom
    access_token = obtener_access_token()
    if not access_token:
        return "No se pudo obtener el token de acceso a Zoom", 500

    # Configuración de la reunión
    meeting_data = {
        "topic": "Reunión para propiedad",
        "type": 2,
        "start_time": fecha_hora_seleccionada,
        "duration": 40,
        "timezone": "America/Santiago",
        "agenda": f"Reunión para discutir la propiedad ID {propiedad_id}",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": False,
            "mute_upon_entry": True,
            "approval_type": 1,
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

        return redirect(url_for('invite', join_url=join_url, topic=topic, start_time=start_time, duration=duration, agenda=agenda))
    else:
        # Incluir el contenido del error para facilitar el debug
        return f"Error al crear la reunión: {response.status_code}, {response.text}", response.status_code

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

    # Obtener el código de empresa del administrador
    codigo_empresa = UsuarioEmpresa.query.filter_by(id_usuario=current_user.id).first()
    
    if not codigo_empresa:
        return "No se pudo obtener el código de empresa del administrador.", 403

    # Obtener todos los usuarios que pertenecen a la misma empresa (mismo codigo_empresa)
    usuarios = Usuario.query.join(UsuarioEmpresa, Usuario.id == UsuarioEmpresa.id_usuario) \
                            .filter(UsuarioEmpresa.codigo_empresa == codigo_empresa.codigo_empresa) \
                            .all()

    # Crear una lista de diccionarios con los detalles de los usuarios
    usuarios_lista = [{'id': usuario.id, 'username': usuario.username, 'email': usuario.email} for usuario in usuarios]

    # Renderizar el template 'invite.html' pasando los detalles de la reunión y la lista de usuarios
    return render_template(
        'invite.html', 
        usuarios=usuarios_lista, 
        join_url=join_url, 
        topic=topic, 
        start_time=start_time, 
        duration=duration, 
        agenda=agenda
    )

@app.route('/enviar_invitaciones', methods=['POST'])
@login_required
def enviar_invitaciones():
    # Recibir correos seleccionados
    correos = request.form.getlist('usuarios')
    join_url = request.form['join_url']

    # Crear un mensaje de invitación
    mensaje = f"Has sido invitado a una reunión. Únete usando este enlace: {join_url}"

    # Buscar cada usuario por correo electrónico y crear una notificación para ellos
    for correo in correos:
        usuario = Usuario.query.filter_by(email=correo).first()
        
        if usuario:
            notificacion = Notificacion(id_usuario=usuario.id, mensaje=mensaje, leido=0)
            db.session.add(notificacion)

    # Confirmar cambios en la base de datos
    db.session.commit()

    # Redirigir después de 5 segundos a invite.html usando JavaScript
    return '''
        <html>
        <head>
            <meta http-equiv="refresh" content="5;url={}"> <!-- Redirige en 5 segundos -->
        </head>
        <body>
            <p>Notificaciones enviadas a los usuarios seleccionados. Serás redirigido a la página de invitaciones en 5 segundos...</p>
        </body>
        </html>
    '''.format(url_for('vista_propiedad'))
    
@app.route('/notificaciones')
@login_required
def notificaciones():
    # Obtener las notificaciones no leídas para el usuario actual
    notificaciones = Notificacion.query.filter_by(id_usuario=current_user.id, leido=0).order_by(Notificacion.fecha.desc()).all()

    return render_template('notificaciones.html', notificaciones=notificaciones)

@app.route('/marcar_leido/<int:id>', methods=['POST'])
@login_required
def marcar_leido(id):
    # Obtener la notificación correspondiente para el usuario actual
    notificacion = Notificacion.query.filter_by(id=id, id_usuario=current_user.id).first()

    if notificacion:
        # Marcar como leída
        notificacion.leido = 1
        db.session.commit()
        flash("Notificación marcada como leída.")
    else:
        flash("No se pudo encontrar la notificación o no tienes permiso para modificarla.")
    
    return redirect(url_for('notificaciones'))

#DESDE ACA COMIENZA LAS RUTAS DEL CRM

#BOTON DASHBOARD DEL SIDEBAR

@app.route('/dashboard-content')
@login_required
def dashboard_content():
    # Consulta para obtener todas las propiedades de la empresa y sus visitas (0 si no existen)
    propiedades_trafico = (
        db.session.query(
            Propiedad.id_propiedad,
            Propiedad.direccion,
            func.count(VisitaPropiedad.id_visita).label('total_visitas')
        )
        .outerjoin(VisitaPropiedad, Propiedad.id_propiedad == VisitaPropiedad.id_propiedad)
        .join(Usuario, Propiedad.id_usuario == Usuario.id)
        .filter(Usuario.empresa == current_user.empresa)
        .group_by(Propiedad.id_propiedad)
        .all()
    )

    # Datos de ejemplo para otras secciones
    weekly_sales = [
        {'type': 'Direct', 'amount': 5856, 'percentage': 55},
        {'type': 'Affiliate', 'amount': 2602, 'percentage': 25},
        {'type': 'Email', 'amount': 1802, 'percentage': 15},
        {'type': 'Other', 'amount': 1105, 'percentage': 5}
    ]
    
    recent_orders = [
        {'product': 'Iphone 5', 'photo': 'https://via.placeholder.com/110x110', 'product_id': '#9405822', 'amount': 1250, 'date': '03 Aug 2017', 'shipping': 90},
        {'product': 'Earphone GL', 'photo': 'https://via.placeholder.com/110x110', 'product_id': '#9405820', 'amount': 1500, 'date': '03 Aug 2017', 'shipping': 60},
        # Más pedidos si es necesario
    ]

    return render_template(
        'dashboard_content.html', 
        propiedades_trafico=propiedades_trafico,
        weekly_sales=weekly_sales, 
        recent_orders=recent_orders
    )

#BOTON SEGUIMIENTO DEL SIDE BAR

@app.route('/seguimiento-content')
@login_required
def seguimiento_content():
    # Obtener el código de empresa del usuario autenticado
    codigo_empresa = (
        db.session.query(UsuarioEmpresa.codigo_empresa)
        .filter(UsuarioEmpresa.id_usuario == current_user.id)
        .scalar()
    )

    # Filtrar las propiedades que pertenecen a la misma empresa
    propiedades = (
        db.session.query(Propiedad.id_propiedad, Propiedad.direccion, Propiedad.comuna, Usuario.username)
        .join(Usuario, Propiedad.id_usuario == Usuario.id)
        .join(UsuarioEmpresa, Usuario.id == UsuarioEmpresa.id_usuario)
        .filter(UsuarioEmpresa.codigo_empresa == codigo_empresa)
        .all()
    )

    return render_template('seguimiento_content.html', propiedades=propiedades)

#BOTON DE EDITAR EMPRESA

@app.route('/edit_company')
@login_required
def edit_company():
    # Obtener la empresa asociada al usuario actual
    empresa = (
        db.session.query(Empresa.nombre_empresa)
        .filter(Empresa.id_usuario == current_user.id)
        .first()
    )

    return render_template('edit_company.html', empresa=empresa)

@app.route('/update_company', methods=['POST'])
@login_required
def update_company():
    data = request.get_json()
    nuevo_nombre = data.get('nombre_empresa')

    # Obtener la empresa asociada al usuario actual
    empresa = Empresa.query.filter_by(id_usuario=current_user.id).first()
    
    # Actualizar el nombre de la empresa si existe
    if empresa:
        empresa.nombre_empresa = nuevo_nombre
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Empresa no encontrada'}), 404

#BOTON GESTION DE USUARIOS
 
@app.route('/gestion_usuarios')
@login_required
def gestion_usuarios():
    # Obtener el código de la empresa del usuario autenticado
    codigo_empresa = UsuarioEmpresa.query.filter_by(id_usuario=current_user.id).first().codigo_empresa

    # Consultar las actividades de los usuarios de la misma empresa
    actividades = LogActividad.query.filter_by(codigo_empresa=codigo_empresa).order_by(LogActividad.fecha_hora.desc()).all()
    
    actividades_lista = [
        {
            'usuario': actividad.usuario.username,
            'accion': actividad.accion,
            'detalle': actividad.detalle,
            'fecha_hora': actividad.fecha_hora.strftime('%Y-%m-%d %H:%M')
        }
        for actividad in actividades
    ]
    # Obtener los usuarios que son miembros de la misma empresa
    usuarios_empresa = (
        db.session.query(Usuario)
        .join(UsuarioEmpresa, Usuario.id == UsuarioEmpresa.id_usuario)
        .filter(UsuarioEmpresa.codigo_empresa == codigo_empresa)
        .all()
    )
    return render_template('gestion_usuarios.html', actividades=actividades_lista, usuarios=usuarios_empresa)


#CHECKBOX PARA OTORGAR ACCESO AL CRM A LOS USUARIOS DE LA EMPRESA QUE NO SEAN ADMINS

@app.route('/modificar_permiso_crm', methods=['POST'])
@login_required
def modificar_permiso_crm():
    usuario_id = request.form.get('usuario_id')
    acceso_crm = request.form.get('acceso_crm') == 'true'
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.acceso_crm = acceso_crm
        db.session.commit()
        flash(f"Permiso de acceso al CRM para {usuario.username} actualizado.")
    else:
        flash("Usuario no encontrado.", "error")
    return redirect(url_for('menu'))

#CHECKBOX PARA OTORGAR PERMISOS PARA EDITAR CUALQUIER PROPIEDAD AL USUARIO

@app.route('/modificar_permiso_editar', methods=['POST'])
@login_required
def modificar_permiso_editar():
    # Obtener el ID del usuario y el valor del permiso desde el formulario
    usuario_id = request.form.get('usuario_id')
    editar_propiedades = request.form.get('editar_propiedades') == 'true'  # Convertir a booleano

    # Buscar el usuario y actualizar el campo editar_propiedades
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.editar_propiedades = editar_propiedades
        db.session.commit()
        flash(f"Permiso de editar todas las propiedades para {usuario.username} actualizado.")
    else:
        flash("Usuario no encontrado.", "error")

    return redirect(url_for('menu'))

#CHECKBOX PARA OTORGAR PERMISOS PARA CREAR REUNIONES ZOOM EN CUALQUIER PROPIEDAD AL USUARIO

@app.route('/modificar_permiso_reuniones', methods=['POST'])
@login_required
def modificar_permiso_reuniones():
    # Obtener el ID del usuario y el valor del permiso desde el formulario
    usuario_id = request.form.get('usuario_id')
    crear_reuniones = request.form.get('crear_reuniones') == 'true'  # Convertir a booleano

    # Buscar el usuario y actualizar el campo crear_reuniones
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.crear_reuniones = crear_reuniones
        db.session.commit()
        flash(f"Permiso de crear reuniones para {usuario.username} actualizado.")
    else:
        flash("Usuario no encontrado.", "error")

    return redirect(url_for('menu'))

@app.route('/agregar_comentario/<int:propiedad_id>', methods=['POST'])
@login_required
def agregar_comentario(propiedad_id):
    comentario_texto = request.form.get('comentario')
    
    # Crear un nuevo comentario
    nuevo_comentario = ComentarioPropiedad(
        id_usuario=current_user.id,
        id_propiedad=propiedad_id,
        texto=comentario_texto,
        fecha_hora=datetime.utcnow()
    )
    
    db.session.add(nuevo_comentario)
    db.session.commit()
    
    flash('Comentario agregado correctamente.')
    return redirect(url_for('portal_propiedad', id_propiedad=propiedad_id))

@app.route('/responder_comentario/<int:comentario_id>', methods=['POST'])
@login_required
def responder_comentario(comentario_id):
    respuesta_texto = request.form.get('respuesta')
    
    # Obtener el comentario padre
    comentario_padre = ComentarioPropiedad.query.get_or_404(comentario_id)
    
    # Crear la respuesta
    respuesta = ComentarioPropiedad(
        id_usuario=current_user.id,
        id_propiedad=comentario_padre.id_propiedad,
        texto=respuesta_texto,
        fecha_hora=datetime.utcnow(),
        id_comentario_padre=comentario_padre.id
    )
    
    db.session.add(respuesta)
    db.session.commit()
    
    flash('Respuesta agregada correctamente.')
    return redirect(url_for('portal_propiedad', id_propiedad=comentario_padre.id_propiedad))
