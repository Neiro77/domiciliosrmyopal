# db_config.py
import psycopg2

DB_HOST = "localhost"  # Reemplaza con tu host si es diferente
DB_NAME = "rm_domicilios_yopal_db"
DB_USER = "postgres"   # Reemplaza con tu usuario de PostgreSQL
DB_PASSWORD = "P4o13C70#.20_/25$"     # Reemplaza con tu contraseña si tienes

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
    return conn
    

# rm_domicilios_yopal/config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta_aqui'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///rm_domicilios.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Flask-Mail para notificaciones
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER') # Tu correo (ej: tuapp@gmail.com)
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS') # La contraseña de aplicación (NO tu contraseña de Gmail)

    # Puedes añadir más configuraciones para la aplicación
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads') # Para futuras cargas de imágenes
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload size