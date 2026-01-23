# rm_domicilios_yopal/admin_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db # Importa db para futuras interacciones con la DB
from models import User, Driver, Business, Order, Customer, OrderStatus, Transaction, TransactionType, OrderItem  # <-- Importa lo nuevo # Importa los modelos necesarios, incluyendo Order y Customer
from sqlalchemy import func # Para usar funciones de agregación como count
from sqlalchemy.orm import joinedload # Para cargar relaciones de forma eficiente
from forms import EmptyForm # Importa el nuevo EmptyForm
from datetime import datetime, time # <--- ¡IMPORTA DATETIME AQUÍ!
from decimal import Decimal

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorador para requerir rol de administrador
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acceso denegado. Solo para administradores.', 'danger')
            return redirect(url_for('public.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Obtener la fecha de hoy
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_end = datetime.combine(datetime.utcnow().date(), time.max)
    
    # Lógica para mostrar un resumen de la administración
    total_users = db.session.scalar(db.select(func.count(User.id)))
    active_users = db.session.scalar(db.select(func.count(User.id)).filter_by(is_active=True))
    pending_drivers = db.session.scalar(db.select(func.count(User.id)).filter_by(role='driver', is_active=False))
    pending_businesses = db.session.scalar(db.select(func.count(User.id)).filter_by(role='business', is_active=False))
    
    # Puedes añadir más contadores si los necesitas para el dashboard
    # total_orders = db.session.scalar(db.select(func.count(Order.id)))
    # active_orders = db.session.scalar(db.select(func.count(Order.id)).filter(Order.status.in_(['Pendiente', 'Aceptado', 'En Preparacion', 'En Camino'])))
    # Regla: Calcular ganancias (20% de los domicilios entregados hoy)
    # --- >>> NUEVA CONSULTA DE GANANCIAS <<< ---
    # Suma todas las transacciones de ganancia del admin para el día de hoy.
    ganancias_hoy = db.session.execute(
        db.select(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type.in_([TransactionType.COMMISSION_EARNING, TransactionType.CANCELLATION_PENALTY_ADMIN]),
            Transaction.timestamp.between(today_start, today_end)
        )
    ).scalar_one_or_none() or Decimal('0.00')
    # Instancia el formulario vacío aquí para el token CSRF si se usa en el dashboard (ej. un formulario de búsqueda)
    form = EmptyForm()

    return render_template('admin/dashboard.html', 
                           total_users=total_users, 
                           active_users=active_users, # Nuevo contador
                           pending_drivers=pending_drivers, 
                           pending_businesses=pending_businesses,
                           ganancias_hoy=ganancias_hoy,
                           form=form)
                           
# @admin_bp.route('/dashboard')
# @admin_required
# def dashboard():
    # # Lógica para mostrar un resumen de la administración
    # total_users = db.session.scalar(db.select(func.count(User.id)))
    # active_users = db.session.scalar(db.select(func.count(User.id)).filter_by(is_active=True))
    # pending_drivers = db.session.scalar(db.select(func.count(User.id)).filter_by(role='driver', is_active=False))
    # pending_businesses = db.session.scalar(db.select(func.count(User.id)).filter_by(role='business', is_active=False))
    
    # # Puedes añadir más contadores si los necesitas para el dashboard
    # # total_orders = db.session.scalar(db.select(func.count(Order.id)))
    # # active_orders = db.session.scalar(db.select(func.count(Order.id)).filter(Order.status.in_(['Pendiente', 'Aceptado', 'En Preparacion', 'En Camino'])))

    # # Instancia el formulario vacío aquí para el token CSRF si se usa en el dashboard (ej. un formulario de búsqueda)
    # form = EmptyForm()

    # return render_template('admin/dashboard.html', 
                           # total_users=total_users, 
                           # active_users=active_users, # Nuevo contador
                           # pending_drivers=pending_drivers, 
                           # pending_businesses=pending_businesses,
                           # form=form)

@admin_bp.route('/users')
@admin_required
def user_management():
    # Obtener todos los usuarios con sus perfiles para mostrar en la tabla
    # Usamos joinedload para cargar los perfiles de forma eficiente
    users = db.session.execute(
        db.select(User)
        .options(
            joinedload(User.customer_profile),
            joinedload(User.driver_profile),
            joinedload(User.business_profile)
        )
        .order_by(User.created_at.desc())
    ).scalars().unique().all() # .unique() para evitar duplicados si hay múltiples relaciones inversas

    form = EmptyForm() # Necesario para el CSRF en el formulario de toggle_active
    return render_template('admin/users.html', users=users, form=form)

@admin_bp.route('/users/<int:user_id>/toggle_active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    form = EmptyForm() # Instancia el formulario para validar CSRF
    if not form.validate_on_submit():
        flash('Error de seguridad. Recargue la página e intente de nuevo.', 'danger')
        return redirect(url_for('admin.user_management'))

    user = db.session.get(User, user_id)
    if user:
        user.is_active = not user.is_active
        
        # Lógica adicional basada en el rol para sincronizar el estado
        if user.role == 'driver':
            driver_profile = db.session.execute(db.select(Driver).filter_by(user_id=user.id)).scalar_one_or_none()
            if driver_profile:
                driver_profile.is_available = user.is_active # Sincroniza disponibilidad con estado activo
        
        elif user.role == 'business':
            business_profile = db.session.execute(db.select(Business).filter_by(user_id=user.id)).scalar_one_or_none()
            if business_profile:
                # Si se desactiva el usuario, poner el negocio en 'Cerrado'
                # Si se activa el usuario, se podría dejar el estado anterior o ponerlo a 'Abierto' por defecto
                business_profile.status = 'Cerrado' if not user.is_active else 'Abierto' # O mantener el estado si se activa
                
        db.session.commit()
        flash(f'Estado de activación para {user.email} cambiado a {user.is_active}.', 'success')
    else:
        flash('Usuario no encontrado.', 'danger')
    return redirect(url_for('admin.user_management'))

# --- Rutas de gestión de Negocios ---
@admin_bp.route('/businesses')
@admin_required
def business_management():
    # Cargamos también el usuario asociado para acceder al email y estado is_active
    businesses = db.session.execute(
        db.select(Business)
        .options(joinedload(Business.user)) # Cargar el objeto User asociado
        .order_by(Business.name)
    ).scalars().all()
    form = EmptyForm() # Necesario para el CSRF en el formulario de toggle
    return render_template('admin/businesses.html', businesses=businesses, form=form)

# --- Rutas de gestión de Motorizados ---
@admin_bp.route('/drivers')
@admin_required
def driver_management():
    # Cargamos también el usuario asociado para acceder al email y estado is_active
    drivers = db.session.execute(
        db.select(Driver)
        .options(joinedload(Driver.user)) # Cargar el objeto User asociado
        .order_by(Driver.first_name)
    ).scalars().all()
    form = EmptyForm() # Necesario para el CSRF en el formulario de toggle
    return render_template('admin/drivers.html', drivers=drivers, form=form)

# --- Rutas de gestión de Pedidos ---
@admin_bp.route('/orders')
@admin_required
def order_management():
    # Cargamos las relaciones necesarias para mostrar la información del pedido
    orders = db.session.execute(
        db.select(Order)
        .options(
            joinedload(Order.user), # Cliente que hizo el pedido
            joinedload(Order.business), # Negocio
            joinedload(Order.driver), # Motorizado asignado (si lo hay)
            joinedload(Order.service), # Tipo de servicio
            joinedload(Order.payment_method) # Método de pago
        )
        .order_by(Order.order_date.desc())
    ).scalars().all()
    form = EmptyForm() # Necesario para el CSRF en el formulario de toggle
    return render_template('admin/orders.html', orders=orders, form=form)


# 1. RUTA PARA ASIGNAR DOMICILIOS (CON FILTRO INTELIGENTE)
# RUTA PARA ASIGNAR DOMICILIOS (CORREGIDA)
@admin_bp.route('/order/<int:order_id>/assign', methods=['GET', 'POST'])
@admin_required
def assign_driver(order_id):
    # Consulta Optimizada para incluir los productos del pedido
    order = db.session.execute(
        db.select(Order)
        .filter_by(id=order_id)
        .options(
            joinedload(Order.business),
            joinedload(Order.user).joinedload(User.customer_profile),
            joinedload(Order.items).joinedload(OrderItem.product),
            # --- >>> LÍNEA CLAVE AÑADIDA <<< ---
            # Carga también los detalles del paquete si el item es de ese tipo.
            joinedload(Order.items).joinedload(OrderItem.paquete_envio)
        )
    # ).scalar_one_or_none()
    ).scalars().unique().one_or_none() # <--- CAMBIO CLAVE AQUÍ: .scalars().unique().one_or_none()

    if not order:
        flash('Pedido no encontrado.', 'danger')
        return redirect(url_for('admin.order_management'))

    form = EmptyForm() 

    if form.validate_on_submit():
        driver_id = request.form.get('driver_id')
        costo_domicilio_str = request.form.get('costo_domicilio')

        if not driver_id or not costo_domicilio_str:
            flash('Debes seleccionar un conductor y especificar el costo del domicilio.', 'danger')
            return redirect(url_for('admin.assign_driver', order_id=order_id))

        try:
            order.driver_id = int(driver_id)
            order.costo_domicilio = Decimal(costo_domicilio_str)
            order.status = OrderStatus.ACCEPTED.value

            db.session.commit()
            flash(f'Pedido #{order.id} asignado exitosamente.', 'success')
            return redirect(url_for('admin.order_management'))
        except (ValueError, TypeError):
            flash('El costo del domicilio debe ser un número válido.', 'danger')
            return redirect(url_for('admin.assign_driver', order_id=order_id))

    available_drivers = db.session.execute(
        db.select(Driver).filter(Driver.is_available == True, Driver.saldo_cuenta > 0)
    ).scalars().all()

    return render_template('admin/assign_driver.html', order=order, drivers=available_drivers, form=form)

# RUTA PARA ASIGNAR DOMICILIOS (VERSIÓN CON DETALLES DE PRODUCTOS)
# @admin_bp.route('/order/<int:order_id>/assign', methods=['GET', 'POST'])
# @admin_required
# def assign_driver(order_id):
    # # --- Consulta Optimizada para incluir los productos del pedido ---
    # order = db.session.execute(
        # db.select(Order)
        # .filter_by(id=order_id)
        # .options(
            # joinedload(Order.business),
            # joinedload(Order.user).joinedload(User.customer_profile),
            # # --- >>> LÍNEA CLAVE AÑADIDA <<< ---
            # # Carga los items del pedido y, para cada item, carga el producto asociado.
            # joinedload(Order.items).joinedload(OrderItem.product)
        # )
    # ).scalar_one_or_none()

    # if not order:
        # flash('Pedido no encontrado.', 'danger')
        # return redirect(url_for('admin.order_management'))

    # # ... (el resto de la función, con la lógica del form y el POST, no cambia) ...
    # form = EmptyForm() 

    # if form.validate_on_submit():
        # # ... (lógica del POST sin cambios) ...
        # pass

    # available_drivers = db.session.execute(
        # db.select(Driver).filter(Driver.is_available == True, Driver.saldo_cuenta > 0)
    # ).scalars().all()
    
    # return render_template('admin/assign_driver.html', order=order, drivers=available_drivers, form=form)