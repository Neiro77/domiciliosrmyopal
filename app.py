# rm_domicilios_yopal/app.py
import sys
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect # Nueva importación
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from extensions import db, login_manager, mail, migrate, moment # <--- ¡CAMBIO CLAVE!
# from config import Config # <-- Si tienes un archivo config.py, descomenta esto

# PRIMERO: Importa db y los modelos desde models.py
from models import User, Customer, Driver, Business, Product, Order, OrderItem, OpeningHour, PaymentMethod, Service, BusinessPaymentMethod, Category, DetallesPaqueteEnvio, DetallesItemCompra # Añadidos todos los modelos definidos # Importa Category ahora también

import os
import requests
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from functools import wraps
import random
import string
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash # Para hashing de contraseñas


# Define tu configuración aquí o impórtala de config.py
class Config:
    WTF_CSRF_ENABLED = True # Habilita la protección CSRF
    SECRET_KEY = 'una-cadena-dificil-de-adivinar_!@#$%^&*()_+' 
    SQLALCHEMY_DATABASE_URI = 'postgresql://neondb_owner:npg_eaFydS6Tt2xv@ep-blue-hat-acgjjxt5-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com' 
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'neiroc.7@gmail.com' 
    MAIL_PASSWORD = 'qhlb iqhq rcls rjmp'
    MAIL_DEFAULT_SENDER = 'neiroc.7@gmail.com'    
    ADMIN_EMAIL = 'nculmay@ucentral.edu.co' # Correo del administrador para notificaciones

# Instancia global de CSRFProtect
csrf = CSRFProtect() # Nueva instancia global

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) 
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI cargada: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app) 
    # ... otras inicializaciones de extensiones
    csrf.init_app(app) # <--- ¡ESTA LÍNEA ES CRUCIAL!
    # ...
    
    login_manager.login_view = 'public.login'
    login_manager.login_message_category = "warning"
    login_manager.needs_refresh_message = ("Por favor, inicia sesión de nuevo para acceder a esta página.")
    login_manager.needs_refresh_message_category = "info"
    
    # MOVIDO AQUÍ: El user_loader debe estar definido después de login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        # Importa User aquí para evitar importaciones circulares en el ámbito global
        return db.session.get(User, int(user_id))
    # El user_loader fue movido al final de models.py para evitar importaciones circulares aquí.
    # No lo repitas aquí.

    # Importar Blueprints DESPUÉS de que todas las extensiones estén inicializadas.
    # El orden aquí es importante.
    from routes import public_bp 
    from customer_routes import customer_bp 
    from driver_routes import driver_bp         
    from business_routes import business_bp     
    from admin_routes import admin_bp # Se asume que este Blueprint existe y está en admin_routes.py

    app.register_blueprint(public_bp) 
    app.register_blueprint(customer_bp, url_prefix='/customer') 
    app.register_blueprint(driver_bp, url_prefix='/driver')     
    app.register_blueprint(business_bp, url_prefix='/business') 
    app.register_blueprint(admin_bp, url_prefix='/admin')      

    # Función para inicializar datos esenciales
    with app.app_context():
        # db.create_all() # Descomentar si no usas Flask-Migrate y quieres que SQLAlchemy cree las tablas al iniciar

        # Insertar servicios si no existen
        if db.session.scalar(db.select(Service).filter_by(name='comidas')) is None:
            db.session.add(Service(name='comidas', description='Servicio de entrega de alimentos'))
            db.session.commit()
            print("DEBUG: Servicio 'comidas' añadido.")
        
        if db.session.scalar(db.select(Service).filter_by(name='paquetes')) is None:
            db.session.add(Service(name='paquetes', description='Envío y recogida de paquetes'))
            db.session.commit()
            print("DEBUG: Servicio 'paquetes' añadido.")
        
        if db.session.scalar(db.select(Service).filter_by(name='compras')) is None:
            db.session.add(Service(name='compras', description='Servicio para realizar compras'))
            db.session.commit()
            print("DEBUG: Servicio 'compras' añadido.")

        # Insertar métodos de pago si no existen
        if db.session.scalar(db.select(PaymentMethod).filter_by(name='efectivo')) is None:
            db.session.add(PaymentMethod(name='efectivo', description='Pago en efectivo al motorizado', is_active=True))
            db.session.commit()
            print("DEBUG: Método de pago 'efectivo' añadido.")

        if db.session.scalar(db.select(PaymentMethod).filter_by(name='tarjeta de Crédito')) is None:
            db.session.add(PaymentMethod(name='tarjeta de Crédito', description='Pago con tarjeta de crédito', is_active=True))
            db.session.commit()
            print("DEBUG: Método de pago 'tarjeta de Crédito' añadido.")
        
        # Opcional: Asegúrate de tener al menos un negocio, cliente o motorizado activo para pruebas
        # Estas comprobaciones son para fines de depuración, no esenciales para el arranque
        if db.session.scalar(db.select(User).filter_by(role='admin', is_active=True)) is None:
            print("ADVERTENCIA: No hay un usuario administrador activo en la base de datos.")
            # Puedes insertar uno aquí si es necesario para el desarrollo
            # from werkzeug.security import generate_password_hash
            # admin_user = User(email='admin@example.com', password_hash=generate_password_hash('adminpass'), role='admin', is_active=True, nombre='Admin', apellido='User', telefono='1234567890')
            # db.session.add(admin_user)
            # db.session.commit()
            # print("DEBUG: Usuario administrador de ejemplo insertado (admin@example.com / adminpass).")
            
        if db.session.scalar(db.select(User).filter_by(role='business', is_active=True)) is None:
             print("ADVERTENCIA: No hay un usuario de negocio activo. Las pruebas de pedido pueden fallar sin uno.")

        if db.session.scalar(db.select(User).filter_by(role='driver', is_active=True)) is None:
             print("ADVERTENCIA: No hay un usuario motorizado activo. Las pruebas de asignación pueden fallar sin uno.")
             
        if db.session.scalar(db.select(User).filter_by(role='customer', is_active=True)) is None:
             print("ADVERTENCIA: No hay un usuario cliente activo. Las pruebas de carrito pueden fallar sin uno.")


    return app
    
if __name__ == '__main__':
    app = create_app()  
    app.run(debug=True)  


# --- ELIMINA ESTAS FUNCIONES, NO DEBEN ESTAR AQUÍ ---
# @login_manager.user_loader
# def load_user(id):
#     return User.query.get(int(id))

# def send_email_notification(recipient_email, subject, template, **kwargs):
#     msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient_email])
#     msg.html = render_template(template, **kwargs)
#     try:
#         mail.send(msg)
#         print(f"Correo enviado a {recipient_email} con asunto: {subject}") 
#         return True
#     except Exception as e:
#         print(f"Error al enviar correo a {recipient_email}: {e}") 
#         return False
    
# Añadir la función al contexto de la aplicación o pasarlo como argumento


# # --- CONFIGURACIÓN DE OPENCAGE GEOCORDER API ---
# OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY', 'b76a29b5b1fe4a11be70d81a9e901bf2') # Mejor usar variable de entorno

# # --- FUNCIONES AUXILIARES ---
# def geocodificar_direccion(direccion):
    # """Geocodifica una dirección usando la API de OpenCage."""
    # if not OPENCAGE_API_KEY:
        # print("Advertencia: La clave de API de OpenCage está vacía. Geocodificación no posible.")
        # flash("Error interno: La clave de API de OpenCage no está configurada.", 'danger')
        # return None, None

    # base_url = "https://api.opencagedata.com/geocode/v1/json"
    # params = {
        # "q": direccion,
        # "key": OPENCAGE_API_KEY,
        # "language": "es",
        # "no_annotations": 1
    # }
    # try:
        # response = requests.get(base_url, params=params)
        # response.raise_for_status() # Lanza un HTTPError para respuestas malas (4xx o 5xx)
        # data = response.json()
        # if data and data['results']:
            # lat = data['results'][0]['geometry']['lat']
            # lng = data['results'][0]['geometry']['lng']
            # return lat, lng
        # else:
            # print(f"No se encontraron coordenadas para la dirección: {direccion}")
            # print(f"Respuesta de la API sin resultados: {data}")
            # flash(f"No se pudieron obtener las coordenadas para la dirección: '{direccion}'. La API no encontró resultados.", 'danger')
            # return None, None
    # except requests.exceptions.RequestException as e:
        # print(f"Error al geocodificar dirección '{direccion}': {e}")
        # if hasattr(e, 'response') and e.response is not None:
            # print(f"Respuesta de la API (código {e.response.status_code}): {e.response.text}")
            # flash(f"Error al conectar con el servicio de geocodificación: {e.response.status_code} - {e.response.text}", 'danger')
        # else:
            # flash(f"Error de red o desconocido al geocodificar la dirección: {e}", 'danger')
        # return None, None

# def calcular_distancia_coordenadas(lat1, lon1, lat2, lon2):
    # """
    # Calcula la distancia en kilómetros entre dos coordenadas geográficas
    # (latitud, longitud) utilizando la fórmula de Haversine.
    # """
    # lat1_rad = radians(lat1)
    # lon1_rad = radians(lon1)
    # lat2_rad = radians(lat2)
    # lon2_rad = radians(lon2)

    # dlon = lon2_rad - lon1_rad
    # dlat = lat2_rad - lat1_rad

    # a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    # c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # R = 6371 # Radio de la Tierra en kilómetros
    # distancia = R * c
    # return distancia

# def calcular_costo_domicilio(distancia_km):
    # """
    # Calcula el costo del domicilio según la distancia en kilómetros
    # basado en los rangos definidos. Retorna un Decimal.
    # """
    # if distancia_km < 0.9:
        # return Decimal('6000')
    # elif 1.0 <= distancia_km <= 1.9:
        # return Decimal('7000')
    # elif 2.0 <= distancia_km <= 2.9:
        # return Decimal('8000')
    # elif 3.0 <= distancia_km <= 3.5:
        # return Decimal('10000')
    # elif 3.6 <= distancia_km <= 4.5:
        # return Decimal('15000')
    # elif 4.6 <= distancia_km <= 5.5:
        # return Decimal('19000')
    # elif 5.6 <= distancia_km <= 6.5:
        # return Decimal('25000')
    # elif 6.6 <= distancia_km <= 7.0:
        # return Decimal('30000')
    # else:
        # print(f"Advertencia: Distancia ({distancia_km:.2f} km) fuera de los rangos de costo definidos.")
        # return None # Indica que no hay un costo definido para esta distancia

# # def enviar_correo(subject, recipients, text_body, html_body=None):
    # # """
    # # Envía un correo electrónico utilizando Flask-Mail.
    # # """
    # # try:
        # # msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=recipients)
        # # msg.body = text_body
        # # if html_body:
            # # msg.html = html_body
        # # mail.send(msg)
        # # print(f"Correo enviado exitosamente a: {recipients}")
        # # return True
    # # except Exception as e:
        # # print(f"Error al enviar correo a {recipients}: {e}")
        # # # Considera no flashear un mensaje al usuario para errores de correo interno
        # # # flash('Hubo un problema al enviar el correo electrónico. Por favor, contacte con el soporte.', 'danger')
        # # return False
# # --- FIN FUNCIONES AUXILIARES ---

# # --- DECORADORES DE AUTENTICACIÓN Y ROLES ---
# def login_required(f):
    # @wraps(f)
    # def decorated_function(*args, **kwargs):
        # if 'usuario_id' not in session:
            # flash('Debes iniciar sesión para acceder a esta página.', 'danger')
            # return redirect(url_for('login'))
        # return f(*args, **kwargs)
    # return decorated_function

# def cliente_required(f):
    # @wraps(f)
    # def decorated_function(*args, **kwargs):
        # if 'rol' not in session or session['rol'] != 'cliente':
            # flash('No tienes permiso para acceder a esta página.', 'danger')
            # return redirect(url_for('home'))
        # return f(*args, **kwargs)
    # return decorated_function

# def motorizado_required(f):
    # @wraps(f)
    # def decorated_function(*args, **kwargs):
        # if 'rol' not in session or session['rol'] != 'motorizado':
            # flash('No tienes permiso para acceder a esta página.', 'danger')
            # return redirect(url_for('home'))
        # return f(*args, **kwargs)
    # return decorated_function

# def admin_required(f):
    # @wraps(f)
    # def decorated_function(*args, **kwargs):
        # if 'rol' not in session or session['rol'] != 'admin':
            # flash('No tienes permiso para acceder a esta página.', 'danger')
            # return redirect(url_for('home'))
        # return f(*args, **kwargs)
    # return decorated_function
# # --- FIN DECORADORES ---

# # --- RUTAS DE AUTENTICACIÓN Y REGISTRO ---
# @app.route('/')
# def home():
    # if 'usuario_id' in session:
        # if session.get('rol') == 'cliente':
            # return redirect(url_for('listar_categorias_producto_cliente')) # Redirige a categorias de producto para cliente
        # elif session.get('rol') == 'motorizado':
            # return redirect(url_for('listar_pedidos_motorizado'))
        # elif session.get('rol') == 'admin':
            # return redirect(url_for('dashboard_admin'))
    # return render_template('/public/index.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
    # if request.method == 'POST':
        # email = request.form['email'].strip()
        # contrasena = request.form['contrasena']

        # usuario = Usuario.obtener_por_email(email)
        
        # if usuario:
            # # Usar check_password_hash para verificar la contraseña
            # if check_password_hash(usuario.contrasena, contrasena): # ASUMIR que contrasena en DB es el hash
                # session['usuario_id'] = usuario.id
                # session['nombre_usuario'] = usuario.nombre
                # session['rol'] = usuario.rol
                # flash('Inicio de sesión exitoso.', 'success')
                # if usuario.rol == 'cliente':
                    # return redirect(url_for('listar_categorias_producto_cliente'))
                # elif usuario.rol == 'motorizado':
                    # return redirect(url_for('listar_pedidos_motorizado'))
                # elif usuario.rol == 'admin':
                    # return redirect(url_for('dashboard_admin'))
                # else:
                    # flash('Rol de usuario desconocido. Por favor, contacte con soporte.', 'danger')
                    # return redirect(url_for('home'))
            # else:
                # flash('Contraseña incorrecta.', 'danger')
        # else:
            # flash('Usuario no encontrado.', 'danger')
    # return render_template('login.html')

# @app.route('/logout')
# @login_required
# def logout():
    # session.clear() # Limpia toda la sesión
    # flash('Has cerrado sesión exitosamente.', 'info')
    # return redirect(url_for('home'))

# @app.route('/registro', methods=['GET', 'POST'])
# def registro():
    # if request.method == 'POST':
        # nombre = request.form['nombre'].strip()
        # apellido = request.form['apellido'].strip()
        # email = request.form['email'].strip()
        # contrasena = request.form['contrasena']
        # telefono = request.form['telefono'].strip()
        
        # if not all([nombre, apellido, email, contrasena, telefono]):
            # flash('Todos los campos son obligatorios.', 'danger')
            # return render_template('registro.html')

        # if Usuario.obtener_por_email(email):
            # flash('El email ya está registrado.', 'danger')
        # else:
            # hashed_password = generate_password_hash(contrasena) # Hashear la contraseña
            # nuevo_usuario = Usuario.crear(nombre, apellido, email, hashed_password, telefono)
            # if nuevo_usuario:
                # flash('Registro exitoso. Por favor, inicia sesión.', 'success')
                # return redirect(url_for('login'))
            # else:
                # flash('Error al registrar usuario.', 'danger')
    # return render_template('registro.html')

# @app.route('/registro_admin', methods=['GET', 'POST'])
# def registro_admin():
    # # Esta ruta debería ser protegida en producción, quizás con un token de registro único o solo accesible internamente.
    # # Por ahora, se permite para pruebas.
    # if request.method == 'POST':
        # nombre = request.form['nombre'].strip()
        # apellido = request.form['apellido'].strip()
        # email = request.form['email'].strip()
        # contrasena = request.form['contrasena']
        # telefono = request.form['telefono'].strip()

        # if not all([nombre, apellido, email, contrasena, telefono]):
            # flash('Todos los campos son obligatorios.', 'danger')
            # return render_template('registro_admin.html')

        # if Usuario.obtener_por_email(email):
            # flash('El email ya está registrado.', 'danger')
        # else:
            # hashed_password = generate_password_hash(contrasena)
            # nuevo_admin = Usuario.crear(nombre, apellido, email, hashed_password, telefono, rol='admin')
            # if nuevo_admin:
                # flash('Registro de administrador exitoso. Por favor, inicia sesión.', 'success')
                # return redirect(url_for('login'))
            # else:
                # flash('Error al registrar administrador.', 'danger')
    # return render_template('registro_admin.html')

# @app.route('/registro_motorizado', methods=['GET', 'POST'])
# # Esta ruta podría ser accesible solo para administradores o tener un proceso de aprobación.
# @admin_required # Requiere que un admin registre motorizados por ahora.
# def registro_motorizado():
    # if request.method == 'POST':
        # nombre = request.form['nombre'].strip()
        # apellido = request.form['apellido'].strip()
        # email = request.form['email'].strip()
        # contrasena = request.form['contrasena']
        # telefono = request.form['telefono'].strip()
        # licencia_conduccion = request.form['licencia_conduccion'].strip()
        # vehiculo = request.form['vehiculo'].strip()

        # if not all([nombre, apellido, email, contrasena, telefono, licencia_conduccion, vehiculo]):
            # flash('Todos los campos son obligatorios.', 'danger')
            # return render_template('registro_motorizado.html')

        # if Usuario.obtener_por_email(email):
            # flash('El email ya está registrado.', 'danger')
        # else:
            # hashed_password = generate_password_hash(contrasena)
            # # Iniciar una transacción para asegurar que ambos inserts se completen
            # try:
                # conn = get_db_connection()
                # with conn.cursor() as cur:
                    # # Crear usuario primero
                    # cur.execute(
                        # "INSERT INTO usuarios (nombre, apellido, email, contrasena, telefono, rol) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                        # (nombre, apellido, email, hashed_password, telefono, 'motorizado')
                    # )
                    # usuario_id = cur.fetchone()[0]

                    # # Crear motorizado asociado
                    # cur.execute(
                        # "INSERT INTO motorizados (usuario_id, licencia_conduccion, vehiculo, disponible) VALUES (%s, %s, %s, TRUE)",
                        # (usuario_id, licencia_conduccion, vehiculo)
                    # )
                # conn.commit()
                # flash('Registro de motorizado exitoso.', 'success')
                # return redirect(url_for('dashboard_admin')) # O a una lista de motorizados
            # except Exception as e:
                # conn.rollback()
                # print(f"Error al registrar motorizado: {e}")
                # flash('Error al registrar motorizado.', 'danger')
            # finally:
                # conn.close()
    # return render_template('admin/registro_motorizado.html') # Asegúrate de tener este template

# # --- FIN RUTAS DE AUTENTICACIÓN Y REGISTRO ---



# ### **Rutas de Administración**


# # --- RUTAS DE ADMINISTRACIÓN ---
# @app.route('/admin/dashboard')
# @admin_required
# def dashboard_admin():
    # total_restaurantes = Restaurante.contar_restaurantes()
    # total_clientes = Usuario.contar_clientes()
    # total_motorizados = Motorizado.contar_motorizados()
    # total_pedidos = Pedido.contar_pedidos()
    # # Asume que esta función existe y retorna un Decimal
    # ganancias_comisiones = Pedido.calcular_ganancias_comisiones() 

    # return render_template('admin/dashboard.html',
                            # total_restaurantes=total_restaurantes,
                            # total_clientes=total_clientes,
                            # total_motorizados=total_motorizados,
                            # total_pedidos=total_pedidos,
                            # ganancias_comisiones=ganancias_comisiones)

# # Gestión de Restaurantes
# @app.route('/admin/restaurantes')
# @admin_required
# def listar_restaurantes_admin():
    # restaurantes = Restaurante.obtener_todos()
    # return render_template('admin/listar_restaurantes.html', restaurantes=restaurantes)

# @app.route('/admin/restaurantes/crear', methods=['GET', 'POST'])
# @admin_required
# def crear_restaurante_admin():
    # if request.method == 'POST':
        # nombre = request.form['nombre'].strip()
        # direccion = request.form['direccion'].strip()
        # telefono = request.form['telefono'].strip()
        # horario_atencion = request.form['horario_atencion'].strip()
        # descripcion = request.form['descripcion'].strip()
        # logo_url = request.form.get('logo_url', '').strip() # Puede ser opcional

        # if not all([nombre, direccion, telefono, horario_atencion]):
            # flash('Nombre, dirección, teléfono y horario de atención son obligatorios.', 'danger')
            # return render_template('admin/crear_restaurante.html')

        # latitud, longitud = geocodificar_direccion(direccion)

        # if latitud is not None and longitud is not None:
            # restaurante = Restaurante.crear(nombre, direccion, telefono, horario_atencion, descripcion, logo_url, latitud, longitud)
            # if restaurante:
                # flash('Restaurante creado exitosamente con coordenadas!', 'success')
                # return redirect(url_for('listar_restaurantes_admin'))
            # else:
                # flash('Error al crear restaurante.', 'danger')
        # else:
            # flash('No se pudieron obtener las coordenadas para la dirección. Por favor, verifica la dirección.', 'danger')
    # return render_template('admin/crear_restaurante.html')

# @app.route('/admin/restaurantes/editar/<int:restaurante_id>', methods=['GET', 'POST'])
# @admin_required
# def editar_restaurante_admin(restaurante_id):
    # restaurante = Restaurante.obtener_por_id(restaurante_id)
    # if not restaurante:
        # flash('Restaurante no encontrado.', 'danger')
        # return redirect(url_for('listar_restaurantes_admin'))

    # if request.method == 'POST':
        # restaurante.nombre = request.form['nombre'].strip()
        # restaurante.direccion = request.form['direccion'].strip()
        # restaurante.telefono = request.form['telefono'].strip()
        # restaurante.horario_atencion = request.form['horario_atencion'].strip()
        # restaurante.descripcion = request.form['descripcion'].strip()
        # restaurante.logo_url = request.form.get('logo_url', '').strip()

        # if not all([restaurante.nombre, restaurante.direccion, restaurante.telefono, restaurante.horario_atencion]):
            # flash('Nombre, dirección, teléfono y horario de atención son obligatorios.', 'danger')
            # return render_template('admin/editar_restaurante.html', restaurante=restaurante)

        # # Re-geocodificar solo si la dirección ha cambiado
        # if restaurante.direccion != restaurante.direccion_original: # Asume que models.py tiene una forma de detectar cambio
            # latitud, longitud = geocodificar_direccion(restaurante.direccion)
            # if latitud is not None and longitud is not None:
                # restaurante.latitud = latitud
                # restaurante.longitud = longitud
            # else:
                # flash('No se pudieron obtener las nuevas coordenadas para la dirección. Se mantendrán las anteriores.', 'warning')
                # # No retorna, permite que la actualización continúe con las coordenadas viejas

        # if restaurante.guardar(): # Asume un método .guardar() que actualiza los datos en DB
            # flash('Restaurante actualizado exitosamente!', 'success')
            # return redirect(url_for('listar_restaurantes_admin'))
        # else:
            # flash('Error al actualizar restaurante.', 'danger')
    # return render_template('admin/editar_restaurante.html', restaurante=restaurante)

# @app.route('/admin/restaurantes/eliminar/<int:restaurante_id>', methods=['POST'])
# @admin_required
# def eliminar_restaurante_admin(restaurante_id):
    # if Restaurante.eliminar(restaurante_id): # Asume un método .eliminar() en models.py
        # flash('Restaurante eliminado exitosamente.', 'success')
    # else:
        # flash('Error al eliminar restaurante. Asegúrate de que no tenga productos asociados.', 'danger')
    # return redirect(url_for('listar_restaurantes_admin'))

# # Gestión de Productos
# @app.route('/admin/restaurante/<int:restaurante_id>/productos')
# @admin_required
# def listar_productos_admin(restaurante_id):
    # restaurante = Restaurante.obtener_por_id(restaurante_id)
    # if not restaurante:
        # flash('Restaurante no encontrado.', 'danger')
        # return redirect(url_for('listar_restaurantes_admin'))
    # productos = Producto.obtener_por_restaurante(restaurante_id)
    # return render_template('admin/listar_productos.html', restaurante=restaurante, productos=productos)

# @app.route('/admin/restaurante/<int:restaurante_id>/productos/crear', methods=['GET', 'POST'])
# @admin_required
# def crear_producto_admin(restaurante_id):
    # restaurante = Restaurante.obtener_por_id(restaurante_id)
    # if not restaurante:
        # flash('Restaurante no encontrado.', 'danger')
        # return redirect(url_for('listar_restaurantes_admin'))

    # categorias = CategoriaComidaProducto.obtener_todos() # Para el selector de categorías

    # if request.method == 'POST':
        # nombre = request.form['nombre'].strip()
        # descripcion = request.form.get('descripcion', '').strip()
        # precio = request.form['precio']
        # stock = request.form['stock']
        # categoria_id = request.form['categoria_id']
        # imagen_url = request.form.get('imagen_url', '').strip()
        # activo = 'activo' in request.form # Checkbox

        # try:
            # precio = Decimal(precio)
            # stock = int(stock)
            # categoria_id = int(categoria_id)
            # if precio <= 0 or stock < 0:
                # raise ValueError("Precio debe ser positivo y stock no negativo.")
        # except ValueError:
            # flash('Precio y stock deben ser números válidos y positivos.', 'danger')
            # return render_template('admin/crear_producto.html', restaurante=restaurante, categorias=categorias)

        # producto = Producto.crear(restaurante_id, nombre, descripcion, precio, stock, categoria_id, imagen_url, activo)
        # if producto:
            # flash('Producto creado exitosamente.', 'success')
            # return redirect(url_for('listar_productos_admin', restaurante_id=restaurante_id))
        # else:
            # flash('Error al crear producto.', 'danger')
    # return render_template('admin/crear_producto.html', restaurante=restaurante, categorias=categorias)

# @app.route('/admin/producto/<int:producto_id>/editar', methods=['GET', 'POST'])
# @admin_required
# def editar_producto_admin(producto_id):
    # producto = Producto.obtener_por_id(producto_id)
    # if not producto:
        # flash('Producto no encontrado.', 'danger')
        # return redirect(url_for('dashboard_admin')) # Redirige a un lugar seguro

    # restaurante = Restaurante.obtener_por_id(producto.restaurante_id)
    # categorias = CategoriaComidaProducto.obtener_todos()

    # if request.method == 'POST':
        # producto.nombre = request.form['nombre'].strip()
        # producto.descripcion = request.form.get('descripcion', '').strip()
        # producto.precio = request.form['precio']
        # producto.stock = request.form['stock']
        # producto.categoria_id = request.form['categoria_id']
        # producto.imagen_url = request.form.get('imagen_url', '').strip()
        # producto.activo = 'activo' in request.form

        # try:
            # producto.precio = Decimal(producto.precio)
            # producto.stock = int(producto.stock)
            # producto.categoria_id = int(producto.categoria_id)
            # if producto.precio <= 0 or producto.stock < 0:
                # raise ValueError("Precio debe ser positivo y stock no negativo.")
        # except ValueError:
            # flash('Precio y stock deben ser números válidos y positivos.', 'danger')
            # return render_template('admin/editar_producto.html', producto=producto, restaurante=restaurante, categorias=categorias)
        
        # # Asume un método guardar() en el modelo Producto
        # if producto.guardar():
            # flash('Producto actualizado exitosamente.', 'success')
            # return redirect(url_for('listar_productos_admin', restaurante_id=producto.restaurante_id))
        # else:
            # flash('Error al actualizar producto.', 'danger')
    # return render_template('admin/editar_producto.html', producto=producto, restaurante=restaurante, categorias=categorias)

# @app.route('/admin/producto/<int:producto_id>/eliminar', methods=['POST'])
# @admin_required
# def eliminar_producto_admin(producto_id):
    # producto = Producto.obtener_por_id(producto_id)
    # if not producto:
        # flash('Producto no encontrado.', 'danger')
        # return redirect(url_for('dashboard_admin'))

    # restaurante_id = producto.restaurante_id
    # if Producto.eliminar(producto_id): # Asume un método eliminar() en el modelo Producto
        # flash('Producto eliminado exitosamente.', 'success')
    # else:
        # flash('Error al eliminar producto.', 'danger')
    # return redirect(url_for('listar_productos_admin', restaurante_id=restaurante_id))

# # Gestión de Categorías de Productos
# @app.route('/admin/categorias')
# @admin_required
# def listar_categorias_admin():
    # categorias = CategoriaComidaProducto.obtener_todos()
    # return render_template('admin/listar_categorias.html', categorias=categorias)

# @app.route('/admin/categorias/crear', methods=['GET', 'POST'])
# @admin_required
# def crear_categoria_admin():
    # if request.method == 'POST':
        # nombre = request.form['nombre'].strip()
        # descripcion = request.form.get('descripcion', '').strip()

        # if not nombre:
            # flash('El nombre de la categoría es obligatorio.', 'danger')
            # return render_template('admin/crear_categoria.html')
        
        # if CategoriaComidaProducto.obtener_por_nombre(nombre): # Asume este método para evitar duplicados
            # flash('Ya existe una categoría con ese nombre.', 'danger')
            # return render_template('admin/crear_categoria.html')

        # categoria = CategoriaComidaProducto.crear(nombre, descripcion)
        # if categoria:
            # flash('Categoría creada exitosamente.', 'success')
            # return redirect(url_for('listar_categorias_admin'))
        # else:
            # flash('Error al crear categoría.', 'danger')
    # return render_template('admin/crear_categoria.html')

# # Gestión de Motorizados
# @app.route('/admin/motorizados')
# @admin_required
# def listar_motorizados_admin():
    # motorizados = Motorizado.obtener_todos_con_info_usuario() # Asume este método
    # return render_template('admin/listar_motorizados.html', motorizados=motorizados)

# @app.route('/admin/motorizado/<int:motorizado_id>/cambiar_disponibilidad', methods=['POST'])
# @admin_required
# def cambiar_disponibilidad_motorizado_admin(motorizado_id):
    # motorizado = Motorizado.obtener_por_id(motorizado_id)
    # if not motorizado:
        # flash('Motorizado no encontrado.', 'danger')
        # return redirect(url_for('listar_motorizados_admin'))
    
    # nuevo_estado_disponible = request.form.get('disponible') == 'true' # Viene de un toggle/checkbox
    # if Motorizado.actualizar_disponibilidad(motorizado_id, nuevo_estado_disponible):
        # flash(f"Disponibilidad de {motorizado.nombre_usuario} actualizada a {'Disponible' if nuevo_estado_disponible else 'No Disponible'}.", 'success')
    # else:
        # flash('Error al actualizar disponibilidad del motorizado.', 'danger')
    # return redirect(url_for('listar_motorizados_admin'))

# # --- RUTAS DE ADMINISTRACIÓN DE PEDIDOS (ya estaban, revisadas y completadas) ---
# @app.route('/admin/pedidos')
# @admin_required
# def listar_pedidos_admin():
    # pedidos = Pedido.obtener_todos_con_info_extendida() # Obtiene todos los pedidos con info de cliente, restaurante y motorizado
    # return render_template('admin/listar_pedidos.html', pedidos=pedidos)

# @app.route('/admin/pedido/<string:pedido_id>')
# @admin_required
# def ver_detalle_pedido_admin(pedido_id):
    # pedido = Pedido.obtener_por_id_con_detalles(pedido_id)
    # if not pedido:
        # flash('Pedido no encontrado.', 'danger')
        # return redirect(url_for('listar_pedidos_admin'))
    
    # historial_estados = HistorialEstadoPedido.obtener_por_pedido(pedido_id)
    # motorizados_disponibles = Motorizado.obtener_disponibles() # Obtener motorizados disponibles
    
    # return render_template('admin/ver_detalle_pedido.html',
                            # pedido=pedido,
                            # historial_estados=historial_estados,
                            # motorizados_disponibles=motorizados_disponibles)

# @app.route('/admin/pedido/<string:pedido_id>/asignar_motorizado', methods=['POST'])
# @admin_required
# def asignar_motorizado_admin(pedido_id):
    # motorizado_id = request.form.get('motorizado_id', type=int)

    # if not motorizado_id:
        # flash('Debe seleccionar un motorizado para asignar.', 'danger')
        # return redirect(url_for('ver_detalle_pedido_admin', pedido_id=pedido_id))

    # pedido = Pedido.obtener_por_id(pedido_id)
    # if not pedido:
        # flash('Pedido no encontrado.', 'danger')
        # return redirect(url_for('listar_pedidos_admin'))

    # # Solo asignar si el pedido está 'Pendiente'
    # if pedido.estado.lower() != 'pendiente':
        # flash(f'No se puede asignar un motorizado a un pedido en estado "{pedido.estado}". Solo pedidos "Pendientes".', 'danger')
        # return redirect(url_for('ver_detalle_pedido_admin', pedido_id=pedido_id))

    # motorizado_obj = Motorizado.obtener_por_id(motorizado_id)
    # if not motorizado_obj or not motorizado_obj.disponible:
        # flash('El motorizado seleccionado no existe o no está disponible.', 'danger')
        # return redirect(url_for('ver_detalle_pedido_admin', pedido_id=pedido_id))

    # try:
        # conn = get_db_connection()
        # with conn.cursor() as cur:
            # # Asegurar que la asignación es atómica
            # cur.execute("UPDATE pedidos SET motorizado_id = %s, estado = %s WHERE id = %s",
                        # (motorizado_id, 'Asignado', pedido_id))
            
            # # Registrar historial de estado
            # cur.execute("INSERT INTO historial_estados_pedido (pedido_id, estado, fecha_cambio, usuario_id_accion) VALUES (%s, %s, NOW(), %s)",
                        # (pedido_id, 'Asignado', session['usuario_id']))
            
            # # Cambiar estado del motorizado a 'Ocupado'
            # cur.execute("UPDATE motorizados SET disponible = FALSE WHERE id = %s", (motorizado_id,))
            # conn.commit()

        # flash('Motorizado asignado exitosamente al pedido.', 'success')
        
        # # Enviar correo al motorizado
        # usuario_motorizado = Usuario.obtener_por_id(motorizado_obj.usuario_id)
        # if usuario_motorizado and usuario_motorizado.email:
            # asunto = f"¡Nuevo Pedido Asignado! - Pedido #{pedido_id}"
            # cuerpo_texto = f"Hola {usuario_motorizado.nombre},\n\nSe te ha asignado un nuevo pedido con ID #{pedido_id}. Por favor, revisa los detalles en tu panel de motorizado.\n\n¡Gracias por tu servicio!"
            # enviar_correo(asunto, [usuario_motorizado.email], cuerpo_texto)
        
        # return redirect(url_for('ver_detalle_pedido_admin', pedido_id=pedido_id))
    # except Exception as e:
        # conn.rollback()
        # print(f"Error al asignar motorizado: {e}")
        # flash('Error al asignar motorizado al pedido.', 'danger')
    # finally:
        # conn.close()
    # return redirect(url_for('ver_detalle_pedido_admin', pedido_id=pedido_id))

# # --- FIN RUTAS DE ADMINISTRACIÓN ---


# ### **Rutas de Cliente**

# # --- RUTAS DE CLIENTE ---
# @app.route('/cliente/categorias_producto_cliente', methods=['GET'])
# @login_required
# @cliente_required
# def listar_categorias_producto_cliente():
    # categorias = CategoriaComidaProducto.obtener_todos()
    # return render_template('cliente/menu_categorias_producto_cliente.html', categorias=categorias)

# # Ruta para manejar la selección de una categoría
# @app.route('/solicitar_domicilio/<int:categoria_id>')
# @login_required
# @cliente_required
# def solicitar_domicilio(categoria_id):
    # # Aquí podríamos filtrar restaurantes por categoría, o simplemente mostrar todos si solo hay una categoría principal
    # # Por ahora, si es la categoría "Restaurantes" (ID 1, asumiendo), redirige a la lista de restaurantes.
    # # Para otras categorías, podrías mostrar productos directamente o una página específica.
    # categoria = CategoriaComidaProducto.obtener_por_id(categoria_id)
    # if not categoria:
        # flash('Categoría no encontrada.', 'danger')
        # return redirect(url_for('listar_categorias_producto_cliente'))

    # # Si la categoría es 'Restaurantes', asumimos que muestra todos los restaurantes.
    # # Podrías tener un campo 'tipo_categoria' en CategoriaComidaProducto para esto.
    # if categoria.nombre.lower() == 'restaurantes': # o categoria_id == ID_DE_CATEGORIA_RESTAURANTES
        # return redirect(url_for('listar_restaurantes_cliente'))
    # else:
        # # Aquí podrías listar productos de esa categoría específica,
        # # o restaurantes que ofrecen productos de esa categoría.
        # # Por ahora, es un placeholder.
        # flash(f"Has elegido el servicio para la categoría: {categoria.nombre}. Lógica por implementar para esta categoría.", 'info')
        # return redirect(url_for('listar_restaurantes_cliente')) # Redirige temporalmente

# @app.route('/cliente/restaurantes')
# @login_required
# @cliente_required
# def listar_restaurantes_cliente():
    # restaurantes = Restaurante.obtener_todos()
    # return render_template('cliente/restaurantes_cliente.html', restaurantes=restaurantes)

# @app.route('/cliente/restaurante/<int:restaurante_id>')
# @login_required
# @cliente_required
# def ver_restaurante_cliente(restaurante_id):
    # restaurante = Restaurante.obtener_por_id(restaurante_id)
    # if not restaurante:
        # flash('Restaurante no encontrado.', 'danger')
        # return redirect(url_for('listar_restaurantes_cliente'))
    
    # # Obtener productos activos y en stock de este restaurante
    # productos = Producto.obtener_por_restaurante_activos_y_en_stock(restaurante_id) # Asume este método
    
    # # Recuperar el carrito de la sesión
    # carrito = session.get('carrito', {})
    
    # # Añadir cantidad al producto si ya está en el carrito para mostrar en la UI
    # for producto in productos:
        # producto.cantidad_en_carrito = carrito.get(str(producto.id), 0)

    # return render_template('cliente/ver_restaurantes_cliente.html', restaurante=restaurante, productos=productos)

# @app.route('/cliente/agregar_al_carrito', methods=['POST'])
# @login_required
# @cliente_required
# def agregar_al_carrito():
    # producto_id = request.form.get('producto_id', type=int)
    # cantidad = request.form.get('cantidad', type=int)

    # if not producto_id or not cantidad or cantidad <= 0:
        # flash('Cantidad o producto inválido.', 'danger')
        # return redirect(request.referrer or url_for('listar_restaurantes_cliente'))

    # producto = Producto.obtener_por_id(producto_id)
    # if not producto or not producto.activo or producto.stock < cantidad:
        # flash('Producto no disponible o stock insuficiente.', 'danger')
        # return redirect(request.referrer or url_for('listar_restaurantes_cliente'))

    # carrito = session.get('carrito', {})
    
    # # Asegurar que el carrito solo contenga productos de un único restaurante
    # if carrito:
        # primer_producto_id_en_carrito = next(iter(carrito)) # Obtener el ID del primer producto en el carrito
        # primer_producto_en_carrito = Producto.obtener_por_id(int(primer_producto_id_en_carrito))
        # if primer_producto_en_carrito and primer_producto_en_carrito.restaurante_id != producto.restaurante_id:
            # # Si el nuevo producto es de un restaurante diferente, vaciar el carrito
            # session['carrito'] = {}
            # carrito = {}
            # flash('Tu carrito ha sido vaciado porque agregaste un producto de un restaurante diferente.', 'warning')
    
    # # Convertir product_id a string para claves de sesión
    # str_producto_id = str(producto_id)
    # carrito[str_producto_id] = carrito.get(str_producto_id, 0) + cantidad
    # session['carrito'] = carrito
    # session.modified = True # Importante para que Flask sepa que la sesión ha cambiado

    # flash(f'"{producto.nombre}" añadido al carrito.', 'success')
    # return redirect(request.referrer or url_for('ver_restaurante_cliente', restaurante_id=producto.restaurante_id))

# @app.route('/cliente/ver_carrito')
# @login_required
# @cliente_required
# def ver_carrito():
    # carrito = session.get('carrito', {})
    # productos_en_carrito = []
    # subtotal = Decimal('0.00')
    # restaurante_id = None
    
    # if not carrito:
        # flash('Tu carrito está vacío.', 'info')
        # return render_template('cliente/carrito.html', productos_en_carrito=[], subtotal=Decimal('0.00'), restaurante=None)

    # for prod_id_str, cantidad in carrito.items():
        # producto = Producto.obtener_por_id(int(prod_id_str))
        # if producto:
            # producto.cantidad_en_carrito = cantidad
            # productos_en_carrito.append(producto)
            # subtotal += producto.precio * Decimal(cantidad)
            # restaurante_id = producto.restaurante_id # Asume todos los productos son del mismo restaurante
        # else:
            # # Eliminar productos inválidos del carrito
            # del carrito[prod_id_str]
            # session['carrito'] = carrito
            # session.modified = True
            # flash(f'Un producto con ID {prod_id_str} no se encontró y fue eliminado del carrito.', 'warning')

    # restaurante = None
    # if restaurante_id:
        # restaurante = Restaurante.obtener_por_id(restaurante_id)
        # if not restaurante:
            # flash('El restaurante de los productos en tu carrito no se encontró.', 'danger')
            # session['carrito'] = {} # Vaciar carrito si el restaurante es inválido
            # session.modified = True
            # return redirect(url_for('listar_restaurantes_cliente'))
        
    # return render_template('cliente/carrito.html', productos_en_carrito=productos_en_carrito, subtotal=subtotal, restaurante=restaurante)

# @app.route('/cliente/actualizar_carrito', methods=['POST'])
# @login_required
# @cliente_required
# def actualizar_carrito():
    # producto_id = request.form.get('producto_id', type=int)
    # nueva_cantidad = request.form.get('cantidad', type=int)

    # carrito = session.get('carrito', {})
    # str_producto_id = str(producto_id)

    # if str_producto_id not in carrito:
        # flash('El producto no está en tu carrito.', 'danger')
        # return redirect(url_for('ver_carrito'))

    # producto = Producto.obtener_por_id(producto_id)
    # if not producto:
        # flash('Producto no encontrado.', 'danger')
        # del carrito[str_producto_id]
        # session['carrito'] = carrito
        # session.modified = True
        # return redirect(url_for('ver_carrito'))

    # if nueva_cantidad <= 0:
        # del carrito[str_producto_id]
        # flash(f'"{producto.nombre}" eliminado del carrito.', 'info')
    # elif producto.stock < nueva_cantidad:
        # flash(f'Solo hay {producto.stock} unidades de "{producto.nombre}" disponibles.', 'warning')
        # carrito[str_producto_id] = producto.stock # Ajustar a stock disponible
    # else:
        # carrito[str_producto_id] = nueva_cantidad
        # flash(f'Cantidad de "{producto.nombre}" actualizada.', 'success')

    # session['carrito'] = carrito
    # session.modified = True
    # return redirect(url_for('ver_carrito'))

# # Rutas de Dirección de Cliente
# @app.route('/cliente/direcciones/crear', methods=['GET', 'POST'])
# @login_required
# @cliente_required
# def crear_direccion_cliente():
    # if request.method == 'POST':
        # direccion_texto = request.form['direccion'].strip()
        # alias = request.form['alias'].strip()
        # cliente_id = session['usuario_id']

        # if not direccion_texto or not alias:
            # flash('La dirección y el alias son obligatorios.', 'danger')
            # return render_template('cliente/crear_direccion.html')

        # latitud, longitud = geocodificar_direccion(direccion_texto)

        # if latitud is not None and longitud is not None:
            # nueva_direccion = DireccionCliente.crear(cliente_id, direccion_texto, alias, latitud, longitud)
            # if nueva_direccion:
                # flash('Dirección guardada exitosamente con coordenadas!', 'success')
                # return redirect(url_for('listar_direcciones_cliente'))
            # else:
                # flash('Error al guardar dirección.', 'danger')
        # else:
            # flash('No se pudieron obtener las coordenadas para la dirección. Por favor, verifica la dirección.', 'danger')
    # return render_template('cliente/crear_direccion.html')

# @app.route('/cliente/direcciones')
# @login_required
# @cliente_required
# def listar_direcciones_cliente():
    # cliente_id = session['usuario_id']
    # direcciones = DireccionCliente.obtener_por_cliente(cliente_id)
    # return render_template('cliente/listar_direcciones.html', direcciones=direcciones)

# # --- RUTA PARA MOSTRAR LA PÁGINA DE CONFIRMACIÓN DEL PEDIDO (FINALIZAR PEDIDO) ---
# @app.route('/cliente/finalizar_pedido/<int:restaurante_id>')
# @login_required
# @cliente_required
# def mostrar_finalizar_pedido(restaurante_id):
    # cliente_id = session['usuario_id']
    # carrito = session.get('carrito', {})

    # if not carrito:
        # flash('Tu carrito está vacío.', 'danger')
        # return redirect(url_for('ver_carrito'))

    # productos_en_carrito = []
    # subtotal = Decimal('0.00')
    # restaurante = Restaurante.obtener_por_id(restaurante_id)

    # if not restaurante:
        # flash('Restaurante no encontrado.', 'danger')
        # return redirect(url_for('listar_restaurantes_cliente'))

    # # Validar que todos los productos del carrito sean del mismo restaurante
    # for prod_id_str, cantidad in carrito.items():
        # producto = Producto.obtener_por_id(int(prod_id_str))
        # if producto and producto.restaurante_id == restaurante_id:
            # producto.cantidad_en_carrito = cantidad
            # productos_en_carrito.append(producto)
            # subtotal += producto.precio * Decimal(cantidad)
        # else:
            # flash(f'Producto con ID {prod_id_str} no encontrado, o no pertenece a este restaurante. Se ha eliminado del carrito.', 'warning')
            # del carrito[prod_id_str] # Eliminar producto inválido del carrito
            # session['carrito'] = carrito # Actualizar sesión
            # session.modified = True
            # return redirect(url_for('ver_carrito')) # Redirigir para que el usuario vea el carrito actualizado

    # if not productos_en_carrito:
        # flash('Tu carrito está vacío o no contiene productos del restaurante seleccionado.', 'danger')
        # return redirect(url_for('ver_carrito'))

    # direcciones_cliente = DireccionCliente.obtener_por_cliente(cliente_id)
    # formas_pago = FormaPago.obtener_todos()

    # costo_domicilio = Decimal('0.00')
    # distancia_km = None

    # # Calcular costo de domicilio si hay direcciones y coordenadas válidas
    # if direcciones_cliente and restaurante.latitud is not None and restaurante.longitud is not None:
        # # Se toma la primera dirección del cliente como la dirección predeterminada de envío para el cálculo inicial.
        # # En el frontend, el usuario seleccionará la dirección final.
        # direccion_principal = direcciones_cliente[0] 
        
        # if direccion_principal.latitud is not None and direccion_principal.longitud is not None:
            # distancia_km = calcular_distancia_coordenadas(
                # float(restaurante.latitud), float(restaurante.longitud),
                # float(direccion_principal.latitud), float(direccion_principal.longitud)
            # )
            # costo_domicilio_calculado = calcular_costo_domicilio(distancia_km)
            # if costo_domicilio_calculado is not None:
                # costo_domicilio = costo_domicilio_calculado
            # else:
                # flash(f"No se pudo calcular el costo de domicilio para esta distancia ({distancia_km:.2f} km).", 'warning')
        # else:
            # flash("Advertencia: La dirección principal del cliente no tiene coordenadas válidas.", 'warning')
    # else:
        # flash("Advertencia: No hay direcciones registradas o el restaurante no tiene coordenadas válidas.", 'warning')

    # total_final = subtotal + costo_domicilio

    # return render_template('cliente/finalizar_pedido.html',
                            # productos_en_carrito=productos_en_carrito,
                            # subtotal=subtotal,
                            # restaurante=restaurante,
                            # direcciones_cliente=direcciones_cliente,
                            # formas_pago=formas_pago,
                            # costo_domicilio=costo_domicilio,
                            # distancia_km=distancia_km,
                            # total_final=total_final)

# # --- RUTA PARA PROCESAR LA CREACIÓN DEL PEDIDO EN LA BD ---
# @app.route('/cliente/procesar_pedido', methods=['POST'])
# @login_required
# @cliente_required
# def procesar_pedido():
    # cliente_id = session['usuario_id']
    # restaurante_id = request.form.get('restaurante_id', type=int)
    # direccion_entrega_id = request.form.get('direccion_id', type=int)
    # forma_pago_id = request.form.get('forma_pago_id', type=int)
    # notas = request.form.get('notas', '').strip()

    # productos_en_carrito_ids = session.get('carrito', {})

    # if not productos_en_carrito_ids:
        # flash('Tu carrito está vacío.', 'danger')
        # return redirect(url_for('ver_carrito'))

    # # Validaciones básicas de entrada
    # if not restaurante_id or not direccion_entrega_id or not forma_pago_id:
        # flash('Datos de pedido incompletos. Por favor, selecciona un restaurante, dirección y forma de pago.', 'danger')
        # return redirect(url_for('mostrar_finalizar_pedido', restaurante_id=restaurante_id))

    # # Validar que la dirección de entrega pertenezca al cliente
    # direccion_cliente_obj = DireccionCliente.obtener_por_id_y_cliente(direccion_entrega_id, cliente_id)
    # if not direccion_cliente_obj:
        # flash('La dirección de entrega seleccionada no es válida para tu cuenta.', 'danger')
        # return redirect(url_for('mostrar_finalizar_pedido', restaurante_id=restaurante_id))

    # restaurante = Restaurante.obtener_por_id(restaurante_id)
    # if not restaurante:
        # flash('Restaurante no encontrado.', 'danger')
        # return redirect(url_for('listar_restaurantes_cliente'))

    # # Calcular totales y validar stock
    # total_productos = Decimal('0.00')
    # productos_para_pedido = []
    # productos_a_reducir_stock = {} # Para almacenar producto_id: cantidad

    # for prod_id_str, cantidad_str in productos_en_carrito_ids.items():
        # producto_id = int(prod_id_str)
        # cantidad = int(cantidad_str)
        
        # producto = Producto.obtener_por_id(producto_id)
        # if not producto or not producto.activo or producto.stock < cantidad:
            # flash(f'El producto "{producto.nombre if producto else prod_id_str}" no está disponible o no hay suficiente stock. '
                  # 'Por favor, ajusta tu carrito.', 'danger')
            # return redirect(url_for('ver_carrito')) # Redirige al carrito para que el usuario corrija

        # if producto.restaurante_id != restaurante_id:
            # flash('Error: El carrito contiene productos de otro restaurante.', 'danger')
            # session['carrito'] = {} # Vaciar carrito
            # session.modified = True
            # return redirect(url_for('listar_restaurantes_cliente'))

        # total_productos += producto.precio * Decimal(cantidad)
        # productos_para_pedido.append({
            # 'producto_id': producto.id,
            # 'cantidad': cantidad,
            # 'precio_unitario': producto.precio
        # })
        # productos_a_reducir_stock[producto.id] = cantidad

    # # Calcular costo de domicilio
    # costo_domicilio = Decimal('0.00')
    # if restaurante.latitud is not None and restaurante.longitud is not None and \
       # direccion_cliente_obj.latitud is not None and direccion_cliente_obj.longitud is not None:
        
        # distancia_km = calcular_distancia_coordenadas(
            # float(restaurante.latitud), float(restaurante.longitud),
            # float(direccion_cliente_obj.latitud), float(direccion_cliente_obj.longitud)
        # )
        # costo_domicilio_calculado = calcular_costo_domicilio(distancia_km)
        # if costo_domicilio_calculado is None:
            # flash('Distancia fuera de los rangos de cálculo de domicilio. No se pudo crear el pedido.', 'danger')
            # return redirect(url_for('mostrar_finalizar_pedido', restaurante_id=restaurante_id))
        # else:
            # costo_domicilio = costo_domicilio_calculado
    # else:
        # flash('Faltan coordenadas para calcular el costo del domicilio (restaurante o dirección del cliente). No se pudo crear el pedido.', 'danger')
        # return redirect(url_for('mostrar_finalizar_pedido', restaurante_id=restaurante_id))

    # total_final = total_productos + costo_domicilio
    
    # # Iniciar una transacción de base de datos
    # conn = None
    # try:
        # conn = get_db_connection()
        # with conn.cursor() as cur:
            # # Generar ID de pedido único
            # pedido_id = Pedido.generar_id_unico() # Asume que este método existe y retorna un string/UUID

            # # Crear el encabezado del pedido
            # cur.execute(
                # "INSERT INTO pedidos (id, cliente_id, restaurante_id, direccion_entrega_id, forma_pago_id, total_productos, costo_domicilio, total_final, notas, estado, fecha_creacion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                # (pedido_id, cliente_id, restaurante_id, direccion_entrega_id, forma_pago_id, total_productos, costo_domicilio, total_final, notas, 'Pendiente')
            # )

            # # Crear detalles del pedido y reducir stock
            # for item in productos_para_pedido:
                # cur.execute(
                    # "INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
                    # (pedido_id, item['producto_id'], item['cantidad'], item['precio_unitario'])
                # )
                # # Reducir stock del producto
                # # NOTA: Si models.Producto.reducir_stock ya maneja su propia conexión, podría ser mejor
                # # llamar a esa función fuera de esta transacción o asegurarse de que use la misma conexión/cursor.
                # # Para simplicidad y control transaccional, lo hacemos directamente aquí con el cursor.
                # cur.execute("UPDATE productos SET stock = stock - %s WHERE id = %s", (item['cantidad'], item['producto_id']))
                
                # # Validar que el stock no sea negativo después de la operación (esto debería ser una restricción DB o validación antes)
                # cur.execute("SELECT stock FROM productos WHERE id = %s", (item['producto_id'],))
                # current_stock = cur.fetchone()[0]
                # if current_stock < 0:
                    # raise ValueError(f"Stock insuficiente para producto ID {item['producto_id']} después de la compra.")

            # # Registrar el estado inicial del pedido
            # cur.execute(
                # "INSERT INTO historial_estados_pedido (pedido_id, estado, fecha_cambio, usuario_id_accion) VALUES (%s, %s, NOW(), %s)",
                # (pedido_id, 'Pendiente', cliente_id)
            # )

            # # Crear registro de pago (asume que el pago es "pendiente" o "completado" al crear el pedido)
            # # Para un sistema real, esto se integraría con una pasarela de pago real.
            # cur.execute(
                # "INSERT INTO pagos (pedido_id, forma_pago_id, monto, estado, fecha_pago) VALUES (%s, %s, %s, %s, NOW())",
                # (pedido_id, forma_pago_id, total_final, 'Pendiente') # O 'Completado' si es pago en línea exitoso
            # )
            
            # conn.commit() # Confirmar todas las operaciones si todo fue exitoso

        # # Limpiar carrito después de un pedido exitoso
        # session.pop('carrito', None)
        # session.modified = True

        # flash(f'Tu pedido #{pedido_id} ha sido creado exitosamente!', 'success')
        
        # # Enviar correo de confirmación al cliente
        # cliente = Usuario.obtener_por_id(cliente_id)
        # if cliente and cliente.email:
            # asunto = f"Confirmación de Pedido #{pedido_id}"
            # cuerpo_texto = (f"Hola {cliente.nombre},\n\nGracias por tu pedido! "
                            # f"Tu pedido con ID #{pedido_id} del restaurante {restaurante.nombre} ha sido recibido y está pendiente de procesamiento.\n\n"
                            # f"Total: ${total_final:.2f}\n\n"
                            # f"Lo mantendremos informado sobre el estado de tu pedido.\n\n"
                            # f"¡Gracias por elegirnos!")
            # enviar_correo(asunto, [cliente.email], cuerpo_texto)
            
        # return redirect(url_for('ver_detalle_pedido_cliente', pedido_id=pedido_id))

    # except Exception as e:
        # if conn:
            # conn.rollback() # Revertir todas las operaciones si algo falla
        # print(f"Error al procesar pedido: {e}")
        # flash(f'Error al procesar tu pedido. Por favor, inténtalo de nuevo. Detalle: {e}', 'danger')
        # return redirect(url_for('mostrar_finalizar_pedido', restaurante_id=restaurante_id))
    # finally:
        # if conn:
            # conn.close()

# @app.route('/cliente/pedidos')
# @login_required
# @cliente_required
# def listar_pedidos_cliente():
    # cliente_id = session['usuario_id']
    # pedidos = Pedido.obtener_pedidos_clientes(cliente_id)
    # return render_template('cliente/listar_pedidos_cliente.html', pedidos=pedidos)

# @app.route('/cliente/pedido/<string:pedido_id>')
# @login_required
# @cliente_required
# def ver_detalle_pedido_cliente(pedido_id):
    # pedido = Pedido.obtener_por_id_con_detalles(pedido_id)
    # if not pedido or pedido.cliente_id != session['usuario_id']:
        # flash('Pedido no encontrado o no tienes permiso para verlo.', 'danger')
        # return redirect(url_for('listar_pedidos_cliente'))

    # historial_estados = HistorialEstadoPedido.obtener_por_pedido(pedido_id)
    # return render_template('cliente/ver_detalle_pedido_cliente.html', pedido=pedido, historial_estados=historial_estados)

# @app.route('/cliente/pedido/<string:pedido_id>/cancelar', methods=['POST'])
# @login_required
# @cliente_required
# def cancelar_pedido_cliente(pedido_id):
    # pedido = Pedido.obtener_por_id_con_detalles(pedido_id) 
    # if not pedido or pedido.cliente_id != session['usuario_id']:
        # flash('Pedido no encontrado o no tienes permiso para cancelarlo.', 'danger')
        # return redirect(url_for('listar_pedidos_cliente'))

    # # Solo permitir cancelar si está en estado 'Pendiente'
    # if pedido.estado.lower() != 'pendiente':
        # flash(f'No se puede cancelar el pedido. Estado actual: {pedido.estado}. Solo se permiten cancelaciones para pedidos "Pendientes".', 'danger')
        # return redirect(url_for('ver_detalle_pedido_cliente', pedido_id=pedido_id))

    # conn = None
    # try:
        # conn = get_db_connection()
        # with conn.cursor() as cur:
            # # Actualizar estado del pedido a 'Cancelado'
            # cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", ('Cancelado', pedido_id))
            
            # # Registrar historial de estado
            # cur.execute("INSERT INTO historial_estados_pedido (pedido_id, estado, fecha_cambio, usuario_id_accion) VALUES (%s, %s, NOW(), %s)",
                        # (pedido_id, 'Cancelado', session['usuario_id']))

            # # Reponer stock de los productos del pedido
            # detalles_pedido = DetallePedido.obtener_por_pedido(pedido_id) # Asume este método
            # for item in detalles_pedido:
                # cur.execute("UPDATE productos SET stock = stock + %s WHERE id = %s", (item.cantidad, item.producto_id))
            
            # conn.commit()
            # flash('Pedido cancelado con éxito y stock repuesto.', 'success')

            # cliente = Usuario.obtener_por_id(session['usuario_id'])
            # if cliente and cliente.email:
                # asunto = f"Cancelación de Pedido #{pedido_id}"
                # cuerpo_texto = f"Hola {cliente.nombre},\n\nTu pedido con ID #{pedido_id} ha sido cancelado.\n\nSi tienes alguna pregunta, contáctanos."
                # enviar_correo(asunto, [cliente.email], cuerpo_texto)
            
            # return redirect(url_for('listar_pedidos_cliente'))
    # except Exception as e:
        # if conn:
            # conn.rollback()
        # print(f"Error al cancelar pedido: {e}")
        # flash(f'Error al cancelar el pedido. Inténtalo de nuevo. Detalle: {e}', 'danger')
        # return redirect(url_for('ver_detalle_pedido_cliente', pedido_id=pedido_id))
    # finally:
        # if conn:
            # conn.close()

# # --- FIN RUTAS DE CLIENTE ---


# ### **Rutas de Motorizado**

# # --- RUTAS DE MOTORIZADO ---
# @app.route('/motorizado/pedidos')
# @login_required
# @motorizado_required
# def listar_pedidos_motorizado():
    # motorizado_id = session.get('usuario_id') # Asume que el ID de usuario es también el ID del motorizado
    
    # # Obtener el objeto Motorizado para verificar su estado de disponibilidad
    # motorizado = Motorizado.obtener_por_usuario_id(motorizado_id) # Asume este método
    # if not motorizado:
        # flash('Tu perfil de motorizado no fue encontrado.', 'danger')
        # return redirect(url_for('home'))

    # # Pedidos asignados a este motorizado (estado 'Asignado', 'En_Camino', 'Entregado')
    # pedidos_asignados = Pedido.obtener_pedidos_motorizado(motorizado.id)

    # # Pedidos disponibles para tomar (estado 'Asignado' sin motorizado o 'Pendiente' si el admin aún no asigna)
    # # Aquí la lógica es más compleja, ya que el admin asigna. Si quieres que el motorizado "tome" pedidos,
    # # necesitarías un estado como 'Disponible_para_Motorizado'
    # # Por simplicidad, asumimos que el admin ya los asigna y el motorizado ve sus asignados.
    
    # return render_template('motorizado/listar_pedidos.html', 
                           # pedidos_asignados=pedidos_asignados, 
                           # motorizado=motorizado)


# @app.route('/motorizado/pedido/<string:pedido_id>')
# @login_required
# @motorizado_required
# def ver_detalle_pedido_motorizado(pedido_id):
    # motorizado_usuario_id = session['usuario_id']
    # motorizado = Motorizado.obtener_por_usuario_id(motorizado_usuario_id)

    # if not motorizado:
        # flash('Perfil de motorizado no encontrado.', 'danger')
        # return redirect(url_for('listar_pedidos_motorizado'))

    # pedido = Pedido.obtener_por_id_con_detalles(pedido_id)
    
    # # Validar que el pedido exista y esté asignado a ESTE motorizado, o que sea un pedido que el motorizado pueda "tomar"
    # if not pedido or (pedido.motorizado_id != motorizado.id and pedido.estado.lower() != 'asignado'): # Asume motorizado_id en Pedido
        # flash('Pedido no encontrado o no tienes permiso para verlo.', 'danger')
        # return redirect(url_for('listar_pedidos_motorizado'))
    
    # historial_estados = HistorialEstadoPedido.obtener_por_pedido(pedido_id)
    
    # # Lógica para mostrar la dirección del cliente (latitud, longitud) y del restaurante
    # # Esto puede usarse para un mapa interactivo.
    # direccion_cliente = DireccionCliente.obtener_por_id_y_cliente(pedido.direccion_entrega_id, pedido.cliente_id) # Asume que el pedido tiene cliente_id
    # restaurante = Restaurante.obtener_por_id(pedido.restaurante_id)

    # return render_template('motorizado/ver_detalle_pedido.html',
                           # pedido=pedido,
                           # historial_estados=historial_estados,
                           # direccion_cliente=direccion_cliente,
                           # restaurante=restaurante)

# @app.route('/motorizado/pedido/<string:pedido_id>/actualizar_estado', methods=['POST'])
# @login_required
# @motorizado_required
# def actualizar_estado_pedido_motorizado(pedido_id):
    # motorizado_usuario_id = session['usuario_id']
    # motorizado = Motorizado.obtener_por_usuario_id(motorizado_usuario_id)
    # if not motorizado:
        # flash('Perfil de motorizado no encontrado.', 'danger')
        # return redirect(url_for('listar_pedidos_motorizado'))

    # pedido = Pedido.obtener_por_id(pedido_id)
    # if not pedido:
        # flash('Pedido no encontrado.', 'danger')
        # return redirect(url_for('listar_pedidos_motorizado'))

    # # Asegurarse de que el motorizado que intenta actualizar sea el asignado al pedido
    # if pedido.motorizado_id != motorizado.id:
        # flash('No tienes permiso para actualizar este pedido.', 'danger')
        # return redirect(url_for('listar_pedidos_motorizado'))
    
    # nuevo_estado = request.form['nuevo_estado'].strip()

    # # Lógica de transición de estados:
    # # 'Asignado' -> 'En_Camino' (motorizado va por el pedido)
    # # 'En_Camino' -> 'Recogido' (motorizado tiene el pedido)
    # # 'Recogido' -> 'Enviado' (motorizado en ruta al cliente)
    # # 'Enviado' -> 'Entregado' (motorizado ha entregado el pedido)
    # # 'En_Camino' / 'Recogido' / 'Enviado' -> 'Problema' (si ocurre un problema)
    
    # estados_validos = ['En_Camino', 'Recogido', 'Enviado', 'Entregado', 'Problema'] # Asegúrate de que estos estados existan en tu modelo Pedido

    # if nuevo_estado not in estados_validos:
        # flash('Estado de pedido inválido.', 'danger')
        # return redirect(url_for('ver_detalle_pedido_motorizado', pedido_id=pedido_id))

    # permitir_actualizacion = False
    # if pedido.estado.lower() == 'asignado' and nuevo_estado == 'En_Camino':
        # permitir_actualizacion = True
    # elif pedido.estado.lower() == 'en_camino' and nuevo_estado == 'Recogido':
        # permitir_actualizacion = True
    # elif pedido.estado.lower() == 'recogido' and nuevo_estado == 'Enviado':
        # permitir_actualizacion = True
    # elif pedido.estado.lower() == 'enviado' and nuevo_estado == 'Entregado':
        # permitir_actualizacion = True
        # # Si se entrega, el motorizado vuelve a estar disponible
        # Motorizado.actualizar_disponibilidad(motorizado.id, True) 
    
    # # Permitir estado "Problema" desde ciertos estados
    # if nuevo_estado == 'Problema' and pedido.estado.lower() in ['asignado', 'en_camino', 'recogido', 'enviado']:
        # permitir_actualizacion = True
        # # Si hay un problema, el motorizado podría volver a estar disponible, o requerir intervención del admin
        # Motorizado.actualizar_disponibilidad(motorizado.id, True)
        
    # if not permitir_actualizacion:
        # flash(f'Transición de estado de "{pedido.estado}" a "{nuevo_estado}" no permitida.', 'danger')
        # return redirect(url_for('ver_detalle_pedido_motorizado', pedido_id=pedido_id))

    # conn = None
    # try:
        # conn = get_db_connection()
        # with conn.cursor() as cur:
            # # Actualizar estado del pedido
            # cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, pedido_id))
            
            # # Registrar historial de estado
            # cur.execute("INSERT INTO historial_estados_pedido (pedido_id, estado, fecha_cambio, usuario_id_accion) VALUES (%s, %s, NOW(), %s)",
                        # (pedido_id, nuevo_estado, motorizado_usuario_id))
            # conn.commit()

        # flash(f'Estado del pedido #{pedido_id} actualizado a "{nuevo_estado}".', 'success')
        
        # # Notificar al cliente sobre el cambio de estado (excepto para 'Recogido' si no es relevante)
        # cliente = Usuario.obtener_por_id(pedido.cliente_id)
        # if cliente and cliente.email:
            # asunto_cliente = f"Actualización de Pedido #{pedido_id}: {nuevo_estado}"
            # cuerpo_texto_cliente = f"Hola {cliente.nombre},\n\nTu pedido con ID #{pedido_id} ahora está en estado: {nuevo_estado}.\n\n¡Gracias por tu paciencia!"
            # enviar_correo(asunto_cliente, [cliente.email], cuerpo_texto_cliente)
            
        # return redirect(url_for('ver_detalle_pedido_motorizado', pedido_id=pedido_id))
    # except Exception as e:
        # if conn:
            # conn.rollback()
        # print(f"Error al actualizar estado del pedido: {e}")
        # flash(f'Error al actualizar el estado del pedido. Detalle: {e}', 'danger')
        # return redirect(url_for('ver_detalle_pedido_motorizado', pedido_id=pedido_id))
    # finally:
        # if conn:
            # conn.close()

# # Ruta para que un motorizado pueda cambiar su disponibilidad
# @app.route('/motorizado/cambiar_estado_disponibilidad', methods=['POST'])
# @login_required
# @motorizado_required
# def cambiar_estado_disponibilidad_motorizado():
    # motorizado_usuario_id = session['usuario_id']
    # motorizado = Motorizado.obtener_por_usuario_id(motorizado_usuario_id)

    # if not motorizado:
        # flash('Perfil de motorizado no encontrado.', 'danger')
        # return redirect(url_for('home'))

    # # Toggle de disponibilidad
    # nuevo_estado_disponible = not motorizado.disponible
    
    # if Motorizado.actualizar_disponibilidad(motorizado.id, nuevo_estado_disponible):
        # flash(f"Tu estado ha sido actualizado a {'Disponible' if nuevo_estado_disponible else 'No Disponible'}.", 'success')
    # else:
        # flash('Error al actualizar tu estado de disponibilidad.', 'danger')
    # return redirect(url_for('listar_pedidos_motorizado'))

# # --- FIN RUTAS DE MOTORIZADO ---

# if __name__ == '__main__':
    # app.run(debug=True)