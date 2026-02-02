# rm_domicilios_yopal/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, TextAreaField, SelectField, DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from models import User, Business, Driver, Customer, PaymentMethod, Address # Importa PaymentMethod y Address
from extensions import db
from flask import current_app # <--- ¡IMPORTA current_app!
from flask_login import current_user # <--- ¡IMPORTA current_user AQUÍ!



class RegistrationForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email(), Length(min=6, max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8, message="La contraseña debe tener al menos 8 caracteres.")])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden.')])
    role = StringField('Rol', validators=[DataRequired()]) #HiddenField('Tipo de Cuenta', validators=[DataRequired()]) # <-- Cámbialo a HiddenField
    # role = SelectField('Registrarse como', choices=[
        # ('customer', 'Cliente'),
        # ('driver', 'Conductor'),
        # ('business', 'Negocio')
    # ], validators=[DataRequired()])
    
    # Campos generales que podrían ser usados por diferentes roles
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=60)])
    phone_number = StringField('Número de Teléfono', validators=[DataRequired(), Length(min=7, max=20)])

    # Campos específicos para Conductores (pueden ser opcionales en el registro inicial si se completan después)
    vehicle_type = StringField('Tipo de Vehículo', validators=[Optional()])
    license_plate = StringField('Placa del Vehículo', validators=[Optional()])

    # Campos específicos para Negocios (pueden ser opcionales en el registro inicial si se completan después)
    business_name = StringField('Nombre del Negocio', validators=[Optional()])
    business_address = StringField('Dirección del Negocio', validators=[Optional()])
    business_description = TextAreaField('Descripción del Negocio', validators=[Optional()])
   
    submit = SubmitField('Registrarse')

    # Validador personalizado para verificar si el email ya existe
    def validate_email(self, email):
        # user = User.query.filter_by(email=email.data).first()
        # if user:
            # raise ValidationError('Ese correo electrónico ya está registrado. Por favor, elige uno diferente.')
            
        _db = current_app.extensions['sqlalchemy'] # <--- ACCESO CORRECTO A DB
        # Usar select() y scalar_one_or_none() para SQLAlchemy 2.0
        user = _db.session.execute(_db.select(User).filter_by(email=email.data)).scalar_one_or_none()
        if user:
            raise ValidationError('Ese email ya está registrado. Por favor, elige uno diferente o inicia sesión.')    
            
# Validador personalizado para el nombre de negocio (si el rol es negocio)
    def validate_business_name(self, field):
        if self.role.data == 'business' and not field.data:
            raise ValidationError('El nombre del negocio es requerido para los registros de negocio.')
        if self.role.data == 'business' and field.data:
            _db = current_app.extensions['sqlalchemy']
            # Convertir el nombre del negocio a slug para buscar duplicados
            # Necesitas una función para generar slugs (ej. slugify de un paquete como python-slugify)
            # Para simplificar aquí, solo verificamos si el nombre existe, pero el slug es para la URL
            from sqlalchemy.exc import NoResultFound
            from models import Business # Asegúrate de importar Business aquí si no lo haces globalmente
            try:
                existing_business = _db.session.execute(_db.select(Business).filter_by(name=field.data)).scalar_one_or_none()
                if existing_business:
                    raise ValidationError('Este nombre de negocio ya está registrado. Por favor, elige otro.')
            except NoResultFound:
                pass # No existe, es un nombre válido
                
# Validadores condicionales para campos específicos de rol
    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        
        # Si la validación básica falla, no sigas con las condicionales
        if not initial_validation:
            return False

        # Si el rol es 'driver', vehicle_type y license_plate son requeridos
        if self.role.data == 'driver':
            if not self.vehicle_type.data:
                self.vehicle_type.errors.append('El tipo de vehículo es requerido para conductores.')
                initial_validation = False
            if not self.license_plate.data:
                self.license_plate.errors.append('La placa del vehículo es requerida para conductores.')
                initial_validation = False
            # Validar que la placa no exista
            if self.license_plate.data:
                _db = current_app.extensions['sqlalchemy']
                from models import Driver
                existing_driver = _db.session.execute(_db.select(Driver).filter_by(license_plate=self.license_plate.data)).scalar_one_or_none()
                if existing_driver:
                    self.license_plate.errors.append('Esta placa ya está registrada.')
                    initial_validation = False

        # Si el rol es 'business', business_name, business_address, business_phone_number son requeridos
        if self.role.data == 'business':
            if not self.business_name.data:
                self.business_name.errors.append('El nombre del negocio es requerido para negocios.')
                initial_validation = False
            if not self.business_address.data:
                self.business_address.errors.append('La dirección del negocio es requerida para negocios.')
                initial_validation = False
            # El phone_number general del formulario se usará para el negocio, ya tiene DataRequired
            
        return initial_validation

class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')
    
# --- >>> NUEVO FORMULARIO PARA REGISTRO RÁPIDO DE CLIENTES <<< ---
class CustomerRegistrationForm(FlaskForm):
    """Formulario simplificado solo para el registro de clientes en la página de login."""
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=60)])
    phone_number = StringField('Número de Teléfono', validators=[DataRequired(), Length(min=7, max=20)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Crear Cuenta de Cliente', name='register_submit')

    def validate_email(self, email):
        user = db.session.execute(db.select(User).filter_by(email=email.data)).scalar_one_or_none()
        if user:
            raise ValidationError('Ese correo electrónico ya está en uso. Por favor, elige otro o inicia sesión.')

# Puedes añadir más formularios aquí (negocio, motorizado, producto, etc.)
class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Restablecimiento de Contraseña')

    def validate_email(self, email):
        _db = current_app.extensions['sqlalchemy'] # <--- ACCESO CORRECTO A DB
        user = _db.session.execute(_db.select(User).filter_by(email=email.data)).scalar_one_or_none()
        if user is None:
            raise ValidationError('No hay cuenta con ese email. Debes registrarte primero.')


class PasswordResetRequestForm(FlaskForm):
    """Formulario para solicitar el restablecimiento de contraseña (solo se pide el email)."""
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Enlace de Restablecimiento')

class ResetPasswordForm(FlaskForm):
    """Formulario para establecer una nueva contraseña (después de recibir el token)."""
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=8, message="La contraseña debe tener al menos 8 caracteres.")])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden.')])
    submit = SubmitField('Restablecer Contraseña')
    
    # Nuevo formulario para añadir/editar direcciones de cliente
class AddressForm(FlaskForm):
    address = StringField('Dirección', validators=[DataRequired(), Length(max=255)])
    alias = StringField('Alias (ej. Casa, Trabajo)', validators=[Optional(), Length(max=100)])
    is_principal = HiddenField('Es Principal', default='False') # Se maneja en el frontend
    latitud = HiddenField('Latitud', validators=[Optional()]) # Para futuras integraciones de mapas
    longitud = HiddenField('Longitud', validators=[Optional()]) # Para futuras integraciones de mapas
    submit = SubmitField('Guardar Dirección')

# Nuevo formulario para el Checkout
class CheckoutForm(FlaskForm):
    
    # --- >>> NUEVO CAMPO PARA RECOGIDA <<< ---
    # Lo añadimos aquí, pero como opcional. La ruta lo hará requerido si es un paquete.
    pickup_address_id = SelectField('Dirección de Recogida', coerce=int, validators=[Optional()])
    
    # SelectField para la dirección de entrega, se llenará dinámicamente
    address_id = SelectField('Selecciona tu Dirección de Entrega', coerce=int, validators=[DataRequired()])
    
    # SelectField para el método de pago, se llenará dinámicamente
    payment_method_id = SelectField('Método de Pago', coerce=int, validators=[DataRequired()])
    
    notes = TextAreaField('Notas Adicionales para el Pedido', validators=[Optional()])
    submit = SubmitField('Confirmar Pedido y Pagar')

    # Validador personalizado para llenar las opciones de direcciones y métodos de pago
    def __init__(self, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        # Llenar las direcciones del usuario actual
        if current_app: # Asegura que estemos en un contexto de aplicación
            # Importa Address y PaymentMethod aquí para evitar circularidad si se usan en otros modelos
            from models import Address, PaymentMethod 
            if current_user.is_authenticated:
                user_addresses = db.session.execute(db.select(Address).filter_by(customer_id=current_user.id)).scalars().all()
                self.address_id.choices = [(addr.id, addr.alias + ": " + addr.address) for addr in user_addresses]
            else:
                self.address_id.choices = [] # Opciones vacías si no está autenticado

            # Llenar los métodos de pago disponibles (asume que todos están disponibles globalmente por ahora)
            available_payment_methods = db.session.execute(db.select(PaymentMethod).filter_by(is_active=True)).scalars().all()
            self.payment_method_id.choices = [(pm.id, pm.name) for pm in available_payment_methods]

# Nuevo formulario para crear un pedido de paquete
class PackageForm(FlaskForm):
    # NUEVOS CAMPOS (los que sí quieres)
    descripcion = TextAreaField(
        'Descripción del paquete',
        validators=[DataRequired(), description='Detalla lo que envías (Ej: Contrato importante, Caja de libros, Pastel de cumpleaños).', Length(max=500)]
    )

    nombre_quien_recibe = StringField(
        'Nombre de quien recibe',
        validators=[DataRequired(), Length(max=100)]
    )

    telefono_quien_recibe = StringField(
        'Teléfono de quien recibe',
        validators=[DataRequired(), Length(min=7, max=20)]
    )
    
    
    # Información general del paquete (esto no cambia)
    tipo_paquete = StringField('Tipo de Paquete', validators=[DataRequired(), Length(max=255)], 
                               description='Ej: Documentos, Ropa, Electrónica, Alimentos no perecederos.')
    # descripcion = TextAreaField('Descripción del Contenido', validators=[DataRequired()], 
                                # description='Detalla lo que envías (Ej: Contrato importante, Caja de libros, Pastel de cumpleaños).')
    tamano_paquete = SelectField('Tamaño Estimado', choices=[
        ('pequeno', 'Pequeño (ej. sobres, documentos)'),
        ('mediano', 'Mediano (ej. caja de zapatos)'),
        ('grande', 'Grande (ej. mochila, caja de electrodoméstico pequeño)')
    ], validators=[DataRequired()], description='Selecciona un tamaño estimado para el paquete.')
    peso_kg = DecimalField('Peso Estimado (kg)', validators=[Optional(), NumberRange(min=0.01)], places=2, 
                           description='Peso aproximado del paquete en kilogramos. (Ej: 0.5, 2.3)')
    dimensiones_cm = StringField('Dimensiones (cm)', validators=[Optional(), Length(max=50)], 
                                 description='Ej: 20x15x10 (largo x ancho x alto) o solo texto.')
    valor_declarado = DecimalField('Valor Declarado (opcional)', validators=[Optional(), NumberRange(min=0.0)], places=2, 
                                   description='Valor asegurado del contenido. Se usará para calcular el costo del seguro.')
    instrucciones_especiales = TextAreaField('Instrucciones Especiales', validators=[Optional()], 
                                            description='Ej: Frágil, Entregar solo a [Nombre], Dejar en portería.')
    
    # --- CAMBIO CLAVE: Convertir campos de dirección a SelectField ---
    # Ahora serán listas desplegables con las direcciones del usuario.
    #direccion_recogida = SelectField('Dirección de Recogida', coerce=int, validators=[DataRequired()],
    #                                 description='Selecciona una de tus direcciones guardadas para la recogida.')
    #direccion_entrega = SelectField('Dirección de Entrega', coerce=int, validators=[DataRequired()],
    #                                description='Selecciona una de tus direcciones guardadas para la entrega.')
    
    precio_calculado = HiddenField('Precio Calculado', validators=[Optional()])

    submit = SubmitField('Añadir paquete al Carrito')

    # --- MÉTODO AÑADIDO: Para cargar dinámicamente las opciones de dirección ---
    # def __init__(self, *args, **kwargs):
        # super(PackageForm, self).__init__(*args, **kwargs)
        # # Llenar las direcciones del usuario actual si está autenticado
        # if current_app and current_user.is_authenticated:
            # # Buscamos el perfil del cliente para acceder a sus direcciones
            # customer_profile = db.session.execute(
                # db.select(Customer).filter_by(user_id=current_user.id)
            # ).scalar_one_or_none()

            # if customer_profile:
                # user_addresses = db.session.execute(
                    # db.select(Address).filter_by(customer_id=customer_profile.id)
                # ).scalars().all()
                
                # # Creamos la lista de opciones (value, label)
                # choices = [(addr.id, addr.full_address) for addr in user_addresses]
                
                # # Asignamos las opciones a ambos campos
                # self.direccion_recogida.choices = choices
                # self.direccion_entrega.choices = choices
            # else:
                # # Si no hay perfil de cliente o direcciones, las opciones estarán vacías
                # self.direccion_recogida.choices = []
                # self.direccion_entrega.choices = []

# Formulario vacío para CSRF en plantillas que no tienen un formulario de datos específico
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit') # Necesita al menos un campo para que csrf_token funcione correctamente

class ToggleAvailabilityForm(FlaskForm):
    submit = SubmitField('Cambiar estado')