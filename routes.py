# rm_domicilios_yopal/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app 
from models import User, Customer, Driver, Business # Asegúrate de que todos los modelos que uses aquí estén importados
from extensions import db # <--- ¡CAMBIO CLAVE! Importa db desde extensions.py
# --- Importamos el nuevo formulario ---
from forms import RegistrationForm, LoginForm, CustomerRegistrationForm, PasswordResetRequestForm, ResetPasswordForm
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message 
import re # Para slugify

# Importaciones adicionales para itsdangerous
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
#from app import db, mail # <-- ¡ELIMINA login_manager de aquí! db y mail están bien

# Helper para generar slugs
def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text) # Elimina caracteres especiales
    text = re.sub(r'[\s_-]+', '-', text)  # Reemplaza espacios/guiones por un solo guion
    text = re.sub(r'^-+|-+$', '', text)   # Elimina guiones al inicio/final
    return text
    
# Crea un Blueprint para las rutas públicas
public_bp = Blueprint('public', __name__)

# --- ELIMINA ESTE BLOQUE: user_loader NO va en routes.py ---
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))
# --------------------------------------------------------

# --- RUTA PRINCIPAL: AHORA REDIRIGE AL LOGIN ---
@public_bp.route('/')
def index():
    # Si el usuario ya está autenticado, lo redirige a su dashboard correspondiente
    if current_user.is_authenticated:
        if current_user.role == 'customer':
            return redirect(url_for('customer.dashboard'))
        elif current_user.role == 'driver':
            return redirect(url_for('driver.dashboard'))
        elif current_user.role == 'business':
            return redirect(url_for('business.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
    # Si no está autenticado, la página principal es el login
    return render_template('public/index.html')

# --- >>> NUEVA RUTA PARA LA PÁGINA DE INICIO PÚBLICA <<< ---
@public_bp.route('/home')
def home():
    """
    Esta ruta renderiza la página de aterrizaje (index.html)
    que contiene información pública sobre el negocio.
    """
    return render_template('public/index.html')
    
# --- PÁGINA DE LOGIN Y REGISTRO DE CLIENTE UNIFICADA ---
@public_bp.route('/login', methods=['GET', 'POST'])
def login():
    # if current_user.is_authenticated:
        # return redirect(url_for('public.index'))        
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'customer':
            return redirect(url_for('customer.dashboard'))
        elif current_user.role == 'driver':
            return redirect(url_for('driver.dashboard'))
        elif current_user.role == 'business':
            return redirect(url_for('business.dashboard'))    

    login_form = LoginForm()
    register_form = CustomerRegistrationForm()

    # --- Lógica para procesar el formulario que se envió ---
    if request.method == 'POST':
        # Revisa qué botón de submit se presionó
        if 'login_submit' in request.form and login_form.validate_on_submit():
            user = db.session.execute(db.select(User).filter_by(email=login_form.email.data)).scalar_one_or_none()
            if user and user.check_password(login_form.password.data):
                if not user.is_active:
                    flash('Tu cuenta no ha sido activada por un administrador.', 'warning')
                    return redirect(url_for('public.login'))
                
                login_user(user)
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('public.index'))
            else:
                flash('Correo electrónico o contraseña incorrectos.', 'danger')

        elif 'register_submit' in request.form and register_form.validate_on_submit():
            try:
                new_user = User(
                    email=register_form.email.data,
                    role='customer',
                    is_active=True
                )
                new_user.set_password(register_form.password.data)
                db.session.add(new_user)
                db.session.commit()

                customer_profile = Customer(
                    user_id=new_user.id,
                    first_name=register_form.first_name.data,
                    last_name=register_form.last_name.data,
                    phone_number=register_form.phone_number.data
                )
                db.session.add(customer_profile)
                db.session.commit()
                
                flash('¡Cuenta de cliente creada! Por favor, inicia sesión.', 'success')
                return redirect(url_for('public.login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ocurrió un error al registrar tu cuenta: {str(e)}', 'danger')
                current_app.logger.error(f"Error de registro de cliente: {e}")

    return render_template('public/login.html', login_form=login_form, register_form=register_form)


# --- PÁGINA DE REGISTRO AVANZADA (PARA TODOS LOS ROLES) ---
@public_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.index')) 

    form = RegistrationForm() 
    
    # Pre-cargar el rol si viene por la URL (ej: /register?role=driver)
    if request.method == 'GET' and request.args.get('role'):
        arg_role = request.args.get('role')
        # Mapeo de roles de la URL a los roles de la base de datos
        role_map = {'restaurant': 'business', 'motorizado': 'driver', 'driver': 'driver', 'business': 'business'}
        form.role.data = role_map.get(arg_role, 'customer')

    if request.method == 'POST':
        current_app.logger.info(f"REGISTER POST: {request.form}")
        current_app.logger.info(f"REGISTER ERRORS: {form.errors}")
        
        current_app.logger.info(f"FORM DATA: {request.form}")
        current_app.logger.info(f"ROLE FIELD: {form.role.data}")

    if form.validate_on_submit():
        # La lógica de creación de usuarios para todos los roles se mantiene aquí
        # (El código que ya tienes para crear customer, driver y business)
        current_app.logger.info("VALID FORM — CREATING USER")

        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            role=form.role.data,
            password_hash=generate_password_hash(form.password.data),
            is_active=form.role.data == 'customer'
        )
        db.session.add(user)
        db.session.flush()  # 🔥 CLAVE
        
        try:
            is_active_user = True if form.role.data == 'customer' else False

            user = User(
                email=form.email.data,
                role=form.role.data,
                is_active=is_active_user
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush() # Para obtener el ID antes del commit
            #db.session.commit()

            if user.role == 'customer':
                customer_profile = Customer(user_id=user.id, first_name=form.first_name.data, last_name=form.last_name.data, phone_number=form.phone_number.data)
                db.session.add(customer_profile)
                flash('Tu cuenta de cliente ha sido creada. ¡Ya puedes iniciar sesión!', 'success')
                return redirect(url_for('public.login'))

            elif user.role == 'driver':
                driver_profile = Driver(user_id=user.id, first_name=form.first_name.data, last_name=form.last_name.data, phone_number=form.phone_number.data, vehicle_type=form.vehicle_type.data, license_plate=form.license_plate.data)
                db.session.add(driver_profile)
                flash('Tu cuenta de conductor ha sido creada y será revisada por un administrador.', 'info')
                return redirect(url_for('public.login'))

            elif user.role == 'business':
                business_slug = slugify(form.business_name.data)
                # ... (lógica para asegurar slug único) ...
                business_profile = Business(user_id=user.id, name=form.business_name.data, address=form.business_address.data, phone_number=form.phone_number.data, description=form.business_description.data, slug=business_slug)
                db.session.add(business_profile)
                flash('Tu cuenta de negocio ha sido creada y será revisada por un administrador.', 'info')
                return redirect(url_for('public.login'))
            
            #db.session.add(profile)
            db.session.commit()
            
            if is_active:
                flash('Registro exitoso. ¡Ya puedes iniciar sesión!', 'success')
            else:
                flash('Registro recibido. Tu cuenta será activada por un administrador pronto.', 'info')
            
            return redirect(url_for('public.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al registrar tu cuenta: {str(e)}', 'danger')
            current_app.logger.error(f"Error de registro: {e}")
            current_app.logger.info(f"FORM ERRORS: {form.errors}")

    return render_template('public/register.html', form=form)


@public_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.login'))
    
    
# --- Función auxiliar para enviar el email (usa la instancia global 'mail') ---
def send_password_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Restablecer Contraseña - RM Domicilios',
                  sender=current_app.config['MAIL_USERNAME'], 
                  recipients=[user.email])
    msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{url_for('public.reset_password', token=token, _external=True)}

Si tú no solicitaste esto, simplemente ignora este mensaje y tu contraseña permanecerá sin cambios.
'''
    try:
        # ACCESO A FLASK-MAIL A TRAVÉS DE current_app.extensions
        current_app.extensions['mail'].send(msg)
        print(f"DEBUG: Correo de restablecimiento enviado a {user.email}")
    except Exception as e:
        print(f"ERROR: No se pudo enviar el correo a {user.email}: {e}")
        flash('Hubo un problema al intentar enviar el correo de restablecimiento. Por favor, inténtalo de nuevo más tarde.', 'danger')

# --- Rutas de Recuperación de Contraseña ---
@public_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        _db = current_app.extensions['sqlalchemy'] 
        user = _db.session.execute(_db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        
        if user:
            send_password_reset_email(user) 
            flash('Si tu correo está en nuestro sistema, recibirás un enlace para restablecer tu contraseña.', 'info')
        else:
            # Aunque el usuario no exista, damos un mensaje genérico por seguridad.
            flash('Si tu correo está en nuestro sistema, recibirás un enlace para restablecer tu contraseña.', 'info')
        return redirect(url_for('public.login')) 

    return render_template('public/forgot_password.html', form=form)

@public_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    # Utiliza el método estático de la clase User para verificar el token y obtener el usuario
    user = User.verify_reset_token(token)

    if user is None: 
        # Si el token es inválido o ha caducado, verify_reset_token ya devuelve None
        # y flash messages ya se manejan en models.py o se pueden añadir aquí si se desea más granularidad
        flash('El token de restablecimiento de contraseña es inválido o ha caducado. Por favor, solicita uno nuevo.', 'warning')
        return redirect(url_for('public.forgot_password')) 

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        
        _db = current_app.extensions['sqlalchemy']
        _db.session.commit() 
        
        flash('Tu contraseña ha sido actualizada. ¡Ya puedes iniciar sesión!', 'success')
        return redirect(url_for('public.login')) 
        
    # Si es una solicitud GET o el formulario no es válido (ej. contraseñas no coinciden)
    return render_template('public/reset_password.html', title='Restablecer Contraseña', form=form)

    
# ... otras rutas como login, register, logout, etc., también deberían usar _db para las operaciones de BD si fuera necesario.
# Por ejemplo, en login:
# user = _db.session.execute(_db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
# Pero la mayoría de las veces, si 'db' está importado de app, los proxies de SQLAlchemy suelen funcionar para estas rutas.
# El problema suele ser con 'db.session.execute' o 'User.query' en momentos específicos de carga.