from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

class Empresa(db.Model):
    __tablename__ = 'empresas'

    codigo_empresa = db.Column(db.String(255), primary_key=True)
    nombre_empresa = db.Column(db.String(255), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    confirmada = db.Column(db.SmallInteger, default=0)

    def __init__(self, codigo_empresa, nombre_empresa, id_usuario, confirmada=False):
        self.codigo_empresa = codigo_empresa
        self.nombre_empresa = nombre_empresa
        self.id_usuario = id_usuario
        self.confirmada = 1 if confirmada else 0  # Convierte booleano a entero

class Favorito(db.Model):
    __tablename__ = 'favoritos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_propiedad = db.Column(db.Integer, db.ForeignKey('system_tabla_propiedades.id_propiedad'), nullable=False)
    fecha_favorito = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def __init__(self, id_usuario, id_propiedad):
        self.id_usuario = id_usuario
        self.id_propiedad = id_propiedad

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)
    leido = db.Column(db.SmallInteger, default=0)
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def __init__(self, id_usuario, mensaje, leido=False):
        self.id_usuario = id_usuario
        self.mensaje = mensaje
        self.leido = leido

class Propiedad(db.Model):
    __tablename__ = 'system_tabla_propiedades'

    id_propiedad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    direccion = db.Column(db.String(255), nullable=False)
    comuna = db.Column(db.String(255), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    modificaciones = db.Column(db.Text, nullable=True)
    codigo_empresa = db.Column(db.String(255), db.ForeignKey('empresas.codigo_empresa'), nullable=True)
    imagen = db.Column(db.String(255), nullable=True)

    def __init__(self, direccion, comuna, id_usuario, modificaciones, codigo_empresa, imagen):
        self.direccion = direccion
        self.comuna = comuna
        self.id_usuario = id_usuario
        self.modificaciones = modificaciones
        self.codigo_empresa = codigo_empresa
        self.imagen = imagen

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(512), nullable=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    admin = db.Column(db.SmallInteger, default=0)
    empresa = db.Column(db.SmallInteger, default=0)

    def __init__(self, username, email, password, admin=False, empresa=False):
        self.username = username
        self.password = password  # Asume que ya es un hash generado previamente
        self.email = email
        self.admin = 1 if admin else 0  # Convertir a entero
        self.empresa = 1 if empresa else 0  # Convertir a entero

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @staticmethod
    def get_by_username(username):
        return Usuario.query.filter_by(username=username).first()

    @staticmethod
    def get_by_id(user_id):
        return Usuario.query.get(int(user_id))
    
    @property
    def is_admin(self):
        return self.admin == 1
    
    def save(self):
        db.session.add(self)
        db.session.commit()

class UsuarioEmpresa(db.Model):
    __tablename__ = 'usuarios_empresas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    codigo_empresa = db.Column(db.String(255), db.ForeignKey('empresas.codigo_empresa'), nullable=True)

    def __init__(self, id_usuario, codigo_empresa):
        self.id_usuario = id_usuario
        self.codigo_empresa = codigo_empresa

class VisitaPropiedad(db.Model):
    __tablename__ = 'visitas_propiedad'

    id_visita = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_propiedad = db.Column(db.Integer, db.ForeignKey('system_tabla_propiedades.id_propiedad'), nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_visita = db.Column(db.DateTime, nullable=True)

    def __init__(self, id_propiedad, id_usuario, fecha_visita):
        self.id_propiedad = id_propiedad
        self.id_usuario = id_usuario
        self.fecha_visita = fecha_visita
