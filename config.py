# rm_domicilios_yopal/config.py
import os

class Config:
    # Asegúrate de que tu SECRET_KEY sea una cadena de bytes
    # La forma más simple es añadir .encode('utf-8') si es un string
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-cadena-dificil-de-adivinar_!@#$%^&*()_+'.encode('utf-8')
    
    # O, si la tienes ya en un archivo de entorno o variable, asegúrate de que sea bytes
    # O si ya sabes que es un string, simplemente asegúrate de que se convierta al usarla
    # Pero lo mejor es que ya esté en bytes en la configuración si la usas mucho.
    
    # Si SECRET_KEY es algo como "random_string_of_characters":
    # SECRET_KEY = b"random_string_of_characters" # Puedes prefijar con 'b' para que sea bytes literal
    # o
    # SECRET_KEY = "random_string_of_characters".encode('utf-8') # Convertirlo a bytes

    # Si usas os.environ.get, el valor que viene de la variable de entorno ya debería ser un str
    # entonces .encode('utf-8') es el camino correcto si no estás seguro del tipo.
    # Por ejemplo, para producción, deberías usar algo como:
    # SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'tu_clave_secreta_de_fallback_para_dev'.encode('utf-8')

    # Para depuración, simplemente asegúrate de que tenga el .encode('utf-8'):
    # SECRET_KEY = 'una_clave_secreta_fuerte_y_aleatoria_para_desarrollo'.encode('utf-8')

    # ... otras configuraciones de la base de datos, correo, etc. ...
    
    # # Configuración de Flask-Mail (solo para referencia, esto está en app.py)
    # MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.googlemail.com'
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'tucorreo@gmail.com' # Reemplaza con tu correo
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'tupassworddeappdegmail' # Reemplaza con tu contraseña de app de Gmail
    # MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME') or 'tucorreo@gmail.com' # O un correo específico
    # --- ¡CAMBIO AQUÍ! ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://postgres:P4o13C70%23.20_%2F25%24@localhost:5432/rm_domicilios_casanare_db'
    # --- FIN DEL CAMBIO ---
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Flask-Mail para notificaciones
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    # Estos deben ser variables de entorno, no cadenas directas.
    # Si los pones directos para prueba, quita os.environ.get:
    # MAIL_USERNAME = 'neiroc.7@gmail.com'
    # MAIL_PASSWORD = 'qhlb iqhq rcls rjmp'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME_ENV', 'neiroc.7@gmail.com') # Si la variable de entorno se llama MAIL_USERNAME_ENV
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD_ENV', 'qhlb iqhq rcls rjmp') # Si la variable de entorno se llama MAIL_PASSWORD_ENV
    #MAIL_USERNAME = os.environ.get('EMAIL_USER', 'neiroc.7@gmail.com') # Pasa el valor por defecto
    #MAIL_PASSWORD = os.environ.get('EMAIL_PASS', 'qhlb iqhq rcls rjmp') # Pasa el valor por defecto

    # Puedes añadir más configuraciones para la aplicación
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024