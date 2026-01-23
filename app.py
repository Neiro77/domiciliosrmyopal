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
    # Intenta leer DATABASE_URL de Render; si no existe, usa la de Neon por defecto
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_eaFydS6Tt2xv@ep-blue-hat-acgjjxt5-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require')
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
        
        try:

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
                 
            # Hacer el commit de todo lo anterior si no hubo errores
            db.session.commit()
             
        except Exception as e:
            # IMPORTANTE: Si falla cualquier consulta por tablas inexistentes, 
            # hacemos rollback y permitimos que la app siga cargando.
            db.session.rollback()
            print(f"AVISO: Omitiendo inicialización de datos (Tablas no listas): {e}")

    return app
    
if __name__ == '__main__':
    app = create_app()  
    app.run(debug=True)  