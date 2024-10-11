import os

class Config:
    DB_USERNAME = 'postgres'
    DB_PASSWORD = 'cfQJCAuZYoWVOWXSDdfvMcWZfBXwxVBL'
    DB_HOST = 'autorack.proxy.rlwy.net'
    DB_PORT = '18665'
    DB_NAME = 'railway'

    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)  # Genera una clave secreta aleatoria
