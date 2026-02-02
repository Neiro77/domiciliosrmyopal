# rm_domicilios_yopal/models.py

import psycopg2
from datetime import datetime, time
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from extensions import db # Importa db desde extensions.py
#from enum import Enum, auto
import enum # Para usar Enum en los estados de pedidos si lo deseas
from decimal import Decimal
import json

# Puedes definir enums para los estados de pedido si lo prefieres para mayor robustez
# Puedes definir enums para los estados de pedido si lo prefieres para mayor robustez
class OrderStatus(enum.Enum):
    PENDING = 'Pendiente'
    ACCEPTED = 'Aceptado'
    PREPARING = 'En Preparacion'
    OUT_FOR_DELIVERY = 'En Camino'
    DELIVERED = 'Entregado'
    CANCELLED = 'Cancelado'

class PaymentStatus(enum.Enum):
    PENDING = 'Pendiente'
    COMPLETED = 'Completado'
    FAILED = 'Fallido'
    REFUNDED = 'Reembolsado'

class TransactionType(enum.Enum):
    DRIVER_RECHARGE = 'Recarga de Conductor'
    COMMISSION_PAYMENT = 'Pago de Comision'
    COMMISSION_EARNING = 'Ganancia por Comision'
    CANCELLATION_PENALTY_DRIVER = 'Compensacion por Cancelacion'
    CANCELLATION_PENALTY_ADMIN = 'Ganancia por Cancelacion'
    # Puedes añadir más tipos en el futuro, ej: PAYOUT_DRIVER, PLATFORM_FEE, etc.


# Tabla de Usuarios (principal)
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer', nullable=False, index=True) # 'customer', 'driver', 'business', 'admin'
    is_active = db.Column(db.Boolean, default=True) # False para driver/business hasta que admin lo active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones con perfiles específicos
    customer_profile = db.relationship('Customer', backref='user', uselist=False, cascade="all, delete-orphan")
    driver_profile = db.relationship('Driver', backref='user', uselist=False, cascade="all, delete-orphan")
    business_profile = db.relationship('Business', backref='user', uselist=False, cascade="all, delete-orphan")
    
    # Relación con pedidos (un usuario puede tener muchos pedidos)
    orders = db.relationship('Order', backref='user', lazy=True)
    # Relación con el historial de estados de pedidos (para saber quién cambió el estado)
    estado_pedidos_historial = db.relationship('HistorialEstadoPedido', backref='usuario_cambio', lazy=True, foreign_keys='HistorialEstadoPedido.usuario_cambio_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Método para generar un token de restablecimiento de contraseña
    def get_reset_token(self, expires_sec=1800): # Token válido por 30 minutos
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    # Método estático para verificar el token de restablecimiento
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return db.session.get(User, user_id) # Usar db.session.get para obtener el usuario por ID

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

# Tabla de Clientes
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True) # Ajustado a nullable
    address = db.Column(db.String(255), nullable=True) # Esta columna debería ser removida y usar la tabla Address
    profile_picture = db.Column(db.String(255), nullable=True)
    # --- >>> NUEVA COLUMNA <<< ---
    deuda_cancelacion = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    
    # Relación a las direcciones del cliente
    addresses = db.relationship('Address', backref='customer', lazy=True, cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Customer {self.first_name} {self.last_name}>"

# Tabla de Conductores
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    vehicle_type = db.Column(db.String(50), nullable=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=True)
    is_available = db.Column(db.Boolean, default=False, index=True) # Por defecto no disponible
    saldo_cuenta = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    current_location = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, default=0.0)
    total_deliveries = db.Column(db.Integer, default=0)
    profile_picture = db.Column(db.String(255), nullable=True)

    # Relación con pedidos (un conductor puede tener muchos pedidos asignados)
    assigned_orders = db.relationship('Order', backref='driver', lazy=True)

    def __repr__(self):
        return f"<Driver {self.first_name} {self.last_name}>"

# Tabla de Negocios
class Business(db.Model):
    __tablename__ = 'businesses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    logo = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Cerrado', index=True) # 'Abierto', 'Cerrado', 'De Vacaciones'
    min_order_value = db.Column(db.Float, default=0.0) # Cambiado a Float para decimales
    delivery_fee = db.Column(db.Float, default=0.0) # Cambiado a Float para decimales
    average_delivery_time = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Float, default=0.0)
    reviews_count = db.Column(db.Integer, default=0)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True) # Para URLs amigables

    # Relaciones con productos, horarios, métodos de pago y pedidos
    products = db.relationship('Product', backref='business', lazy=True, cascade="all, delete-orphan")
    opening_hours = db.relationship('OpeningHour', backref='business', lazy=True, cascade="all, delete-orphan")
    business_payment_methods = db.relationship('BusinessPaymentMethod', backref='business', lazy=True, cascade="all, delete-orphan")
    business_categories = db.relationship('BusinessCategory', backref='business', lazy=True, cascade="all, delete-orphan")
    # Pedidos que recibe el negocio - Usamos back_populates
    orders_received = db.relationship('Order', back_populates='business', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Business {self.name}>"

# Tabla de Productos
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False) # Cambiado a Float
    image_url = db.Column(db.String(255), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True) # Un producto puede tener una categoría
    category = db.relationship('Category', backref='products_in_category', lazy=True)

    def __repr__(self):
        return f"<Product {self.name} from Business {self.business_id}>"

# Tabla de Categorías (ej. Comida, Farmacia, Abarrotes - global para productos)
class Category(db.Model):
    __tablename__ = 'categories' # Renombrado de categorias_comida_producto para ser más general
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Category {self.name}>"

# Tabla de Servicios (Generaliza los tipos de servicio como 'Comida', 'Paquetes', 'Compras')
class Service(db.Model): # Nueva tabla 'services'
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Service {self.name}>"

# Tabla de Relación entre Negocios y Categorías (ej. un negocio puede estar en varias categorías)
class BusinessCategory(db.Model):
    __tablename__ = 'business_categories'
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)

    category = db.relationship('Category', backref='business_associations')

    def __repr__(self):
        return f"<Business {self.business_id} in Category {self.category_id}>"

# Tabla de Direcciones de Cliente (CORREGIDA)
class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    alias = db.Column(db.String(100), nullable=True)
    is_principal = db.Column(db.Boolean, default=False)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

    @property
    def full_address(self):
        # CORRECCIÓN: Se eliminó la lógica que intentaba acceder a 'self.notes',
        # ya que el campo 'notes' pertenece al pedido (Order), no a la dirección (Address).
        parts = []
        if self.alias:
            parts.append(f"{self.alias}:")
        
        parts.append(self.address)
        
        return " ".join(parts)

    def __repr__(self):
        return f"<Address {self.full_address}>"


# Tabla de Pedidos
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True) # Cliente que hizo el pedido
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True, index=True) # Negocio del que se hizo el pedido (opcional)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True, index=True) # Conductor asignado (puede ser nulo al inicio)
    servicio_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, index=True) # Tipo de servicio del pedido
    
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default=OrderStatus.PENDING.value, nullable=False) # Usa el valor del Enum
    total_amount = db.Column(db.Float, nullable=False) # Cambiado a Float
    costo_domicilio = db.Column(db.Float, default=0.0) # Cambiado a Float
    delivery_address = db.Column(db.String(255), nullable=False) # La dirección de texto real de la entrega
    direccion_entrega_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True) # FK a la dirección del cliente
    payment_status = db.Column(db.String(50), default=PaymentStatus.PENDING.value, nullable=False) # Usa el valor del Enum
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=True) # Método de pago usado
    notes = db.Column(db.Text, nullable=True)

    # --- >>> NUEVAS COLUMNAS PARA DIRECCIÓN DE RECOGIDA <<< ---
    # La dirección de recogida es opcional (nullable=True) porque los pedidos
    # de comida no la necesitan; su recogida es el propio negocio.
    pickup_address = db.Column(db.String(255), nullable=True)
    direccion_recogida_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True)

    # Relaciones con los ítems del pedido
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payment_method = db.relationship('PaymentMethod', backref='orders_using_method', lazy=True)
    service = db.relationship('Service', backref='orders_of_service', lazy=True) # Relación con la tabla Service
    #delivery_address_obj = db.relationship('Address', backref='orders_delivered_to', lazy=True) # Relación a la dirección específica
    delivery_address_obj = db.relationship('Address', foreign_keys=[direccion_entrega_id], backref='orders_delivered_to', lazy=True)
    # Relación explícita de Order a Business
    business = db.relationship('Business', foreign_keys=[business_id], back_populates='orders_received')
    # NUEVA RELACIÓN PARA EL HISTORIAL DE ESTADOS
    history = db.relationship('HistorialEstadoPedido', backref='order', lazy=True, cascade="all, delete-orphan")
        # NUEVO
    #paquete_envio = db.relationship('DetallesPaqueteEnvio', back_populates='order', uselist=False)        
    # --- >>> NUEVA RELACIÓN PARA LA DIRECCIÓN DE RECOGIDA <<< ---
    pickup_address_obj = db.relationship('Address', foreign_keys=[direccion_recogida_id], backref='orders_picked_up_from', lazy=True)

    def __repr__(self):
        return f"<Order {self.id} Status: {self.status}>"
           

# Tabla de Ítems del Pedido
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    
    tipo_item = db.Column(db.String(50), nullable=False) # 'producto_comida', 'paquete_envio', 'item_lista_compra'
    quantity = db.Column(db.Integer, nullable=False)
    price_at_order = db.Column(db.Float, nullable=False) # Precio del producto en el momento del pedido (cambiado a Float)

    # Claves foráneas condicionales (solo una de ellas estará llena por detalle)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True) # Para ítems de comida
    paquete_envio_id = db.Column(db.Integer, db.ForeignKey('detalles_paquete_envio.id'), nullable=True) # Para ítems de paquete
    item_compra_id = db.Column(db.Integer, db.ForeignKey('detalles_item_compra.id'), nullable=True) # Para ítems de compra

    product = db.relationship('Product', backref='order_items_product', lazy=True)
    paquete_envio = db.relationship('DetallesPaqueteEnvio', backref='order_items_paquete', lazy=True)
    item_compra = db.relationship('DetallesItemCompra', backref='order_items_compra', lazy=True)

    # Restricción para asegurar que solo una de las FKs de ítem esté llena
    __table_args__ = (
        db.CheckConstraint(
            """
            (product_id IS NOT NULL AND paquete_envio_id IS NULL AND item_compra_id IS NULL AND tipo_item = 'producto_comida') OR
            (product_id IS NULL AND paquete_envio_id IS NOT NULL AND item_compra_id IS NULL AND tipo_item = 'paquete_envio') OR
            (product_id IS NULL AND paquete_envio_id IS NULL AND item_compra_id IS NOT NULL AND tipo_item = 'item_lista_compra')
            """,
            name='chk_one_item_type'
        ),
    )

    def __repr__(self):
        return f"<OrderItem Order: {self.order_id}, Type: {self.tipo_item}, Qty: {self.quantity}>"

# Tabla de Métodos de Pago (ej. Efectivo, Tarjeta de Crédito, PSE)
class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False) # Ej: Efectivo, Tarjeta de Crédito
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True) # Si el método de pago está activo o no

    def __repr__(self):
        return f"<PaymentMethod {self.name}>"

# Tabla de Relación entre Negocios y Métodos de Pago (qué métodos acepta cada negocio)
class BusinessPaymentMethod(db.Model):
    __tablename__ = 'business_payment_methods'
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), primary_key=True)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id', ondelete='CASCADE'), primary_key=True)

    payment_method = db.relationship('PaymentMethod', backref='business_associations')

    def __repr__(self):
        return f"<Business {self.business_id} accepts Payment {self.payment_method_id}>"

# Tabla de Horarios de Apertura del Negocio
class OpeningHour(db.Model):
    __tablename__ = 'opening_hours'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    day_of_week = db.Column(db.String(10), nullable=False) # Ej: Lunes, Martes
    open_time = db.Column(db.Time, nullable=False) # Uso db.Time
    close_time = db.Column(db.Time, nullable=False) # Uso db.Time

    def __repr__(self):
        return f"<OpeningHour Business: {self.business_id}, Day: {self.day_of_week}, Open: {self.open_time}, Close: {self.close_time}>"

# Tabla de Detalles de Paquetes de Envío
class DetallesPaqueteEnvio(db.Model):
    __tablename__ = 'detalles_paquete_envio'
    id = db.Column(db.Integer, primary_key=True)
    # NUEVOS CAMPOS (los que quieres)
    descripcion = db.Column(db.Text, nullable=True)

    nombre_quien_recibe = db.Column(db.String(100), nullable=False)
    telefono_quien_recibe = db.Column(db.String(20), nullable=False)
    
    # CAMPOS ANTIGUOS (SE DEJAN, pero no se usan)
    tipo_paquete = db.Column(db.String(255), nullable=False)
    #direccion_recogida = db.Column(db.Text, nullable=False)
    #direccion_entrega = db.Column(db.Text, nullable=False)
    #descripcion = db.Column(db.Text, nullable=True)
    tamano_paquete = db.Column(db.String(20), nullable=True)
    peso_kg = db.Column(db.Float, nullable=True)
    dimensiones_cm = db.Column(db.String(50), nullable=True)
    valor_declarado = db.Column(db.Float, nullable=True)
    instrucciones_especiales = db.Column(db.Text, nullable=True)
    precio_calculado = db.Column(db.Float, nullable=False)
    # NUEVO
    # order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    # servicio_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    # order = db.relationship('Order', back_populates='paquete_envio')
    
    #origen_address = db.relationship('Address', foreign_keys=[origen_direccion_id], backref='paquetes_origen', lazy=True)
    #destino_address = db.relationship('Address', foreign_keys=[destino_direccion_id], backref='paquetes_destino', lazy=True)

    def __repr__(self):
        return f"<DetallesPaqueteEnvio {self.id}>"

# Tabla de Detalles de Ítems de Compra
class DetallesItemCompra(db.Model): # Renombrado a camelCase
    __tablename__ = 'detalles_item_compra' # Nombre de la tabla en snake_case
    id = db.Column(db.Integer, primary_key=True)
    descripcion_item = db.Column(db.Text, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_estimado = db.Column(db.Float, nullable=True)
    notas_especificas = db.Column(db.Text, nullable=True)
    tienda_preferida = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<DetallesItemCompra {self.id} Desc: {self.descripcion_item}>"

class HistorialEstadoPedido(db.Model):
    __tablename__ = 'historial_estados_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False) # CORRECCIÓN: FK a 'orders.id'
    estado = db.Column(db.String(50), nullable=False)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow) # CORRECCIÓN: Usar datetime.utcnow
    usuario_cambio_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Quién realizó el cambio
    
    # La relación 'order' se define en el modelo Order, backref apunta aquí

    def __repr__(self):
        return f"HistorialEstadoPedido(Pedido: {self.pedido_id}, Estado: {self.estado}, Fecha: {self.fecha_cambio})"
        
        
        
        
# --- >>> NUEVO MODELO DE TRANSACCIONES <<< ---
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    
    # El usuario al que pertenece esta transacción (puede ser un admin o un conductor)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # El pedido que originó esta transacción (opcional)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    
    # El monto de la transacción. Positivo para créditos (ganancias, recargas), negativo para débitos (pagos de comisión).
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # El tipo de transacción, usando el Enum que definimos arriba.
    type = db.Column(db.Enum(TransactionType), nullable=False)
    
    # Descripción para que sea fácil de entender en un historial.
    description = db.Column(db.String(255), nullable=False)
    
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='transactions')
    order = db.relationship('Order', backref='transactions')

    def __repr__(self):
        return f"<Transaction {self.id} | {self.type.value} | {self.amount}>"        
        
        
     # ... (justo después de la clase Transaction) ...
def create_transaction(user_id, amount, trans_type, description, order_id=None):
        """Función de ayuda para crear y guardar una transacción de forma segura."""
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=trans_type,
            description=description,
            order_id=order_id
        )
        db.session.add(transaction)