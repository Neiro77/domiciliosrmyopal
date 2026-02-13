from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, abort, jsonify
from flask_login import login_required, current_user
from models import User, Driver, Order, Business, OrderStatus, Customer, Product, OrderItem, DetallesPaqueteEnvio, Service, TransactionType, create_transaction, Notification # <-- Importa lo nuevo # Importa modelos necesarios y OrderStatus Enum
from functools import wraps # <--- ¡IMPORTA ESTO!
from extensions import db, mail # Importa db para futuras interacciones con la DB
from sqlalchemy.orm import joinedload # Para cargar relaciones eficientemente
from flask_mail import Message # Para construir mensajes de correo
from forms import EmptyForm, ToggleAvailabilityForm, AcceptOrderForm # <--- Importa el nuevo EmptyForm
from datetime import datetime # <--- ¡IMPORTA DATETIME AQUÍ!
from sqlalchemy.sql import func # Para usar funciones de SQL como now()
from decimal import Decimal # Importar Decimal para manejar valores monetarios
from utils.notifications import notify
from app import csrf

driver_bp = Blueprint('driver', __name__, url_prefix='/driver')

# --- Utilidades de Email (Para simplificar, se incluye aquí. En una app grande, sería un módulo separado) ---
def send_email(to_email, subject, template_name, **kwargs):
    try:
        # CORRECCIÓN: Especificar el remitente explícitamente
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender:
            current_app.logger.error("MAIL_DEFAULT_SENDER no está configurado en app.py. No se puede enviar el email.")
            return

        msg = Message(subject, recipients=[to_email], sender=sender) # <--- AHORA EL REMITENTE SE ESPECIFICA AQUÍ
        # Renderiza la plantilla HTML para el cuerpo del email
        # Necesitarás crear estas plantillas en templates/emails/
        msg.html = render_template(f'emails/{template_name}.html', **kwargs)
        mail.send(msg)
        current_app.logger.info(f"Email enviado a {to_email} con asunto: {subject}")
    except Exception as e:
        current_app.logger.error(f"Error al enviar email a {to_email}: {e}")
        # flash(f"Error al enviar notificación por email a {to_email}.", 'danger') # No flashear en el flujo normal



# Decorador para requerir rol de conductor
def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('public.login', next=request.url))
        
        # DEBUG: Esto saldrá en tus logs de Render
        print(f"DEBUG AUTH: Usuario {current_user.email} intentando acceder con rol: {current_user.role}")
        
        if current_user.role != 'driver':
            current_app.logger.warning(
                f"[DRIVER_REQUIRED] role={current_user.role}"
            )
            print(f"DEBUG AUTH: Acceso denegado. Rol '{current_user.role}' no es 'driver'")
            abort(403)  # ✅ CLAVE

        return f(*args, **kwargs)
    return decorated_function

def driver_has_active_order(driver_id):
    return Order.query.filter(
        Order.driver_id == driver_id,
        Order.status.notin_([
            OrderStatus.DELIVERED.value,
            OrderStatus.CANCELLED.value
        ])
    ).first() #is not None
    
def can_transition(current_status, new_status):
    allowed = {
        OrderStatus.PENDING.value: [
            OrderStatus.ACCEPTED.value
        ],
        OrderStatus.ACCEPTED.value: [
            OrderStatus.OUT_FOR_DELIVERY.value
        ],
        OrderStatus.OUT_FOR_DELIVERY.value: [
            OrderStatus.DELIVERED.value
        ]
    }
    return new_status in allowed.get(current_status, [])
    

@driver_bp.route('/dashboard')
@login_required
@driver_required
@csrf.exempt
def dashboard():
    """
    Muestra el dashboard principal del conductor con sus pedidos activos.
    """
    form = EmptyForm()
    # if not form.validate_on_submit():
        # flash('Error de seguridad.', 'danger')
        # return redirect(url_for('driver.dashboard'))

    # 1️⃣ Obtener perfil del conductor (PRIMERO)
    driver_profile = db.session.execute(
        db.select(Driver).filter_by(user_id=current_user.id)
    ).scalar_one_or_none()

    # if not driver_profile:
        # current_app.logger.warning(
            # f"Usuario {current_user.id} tiene rol driver pero no perfil Driver."
        # )
        # flash("Tu perfil de conductor no está completo. Contacta al administrador.", "warning")
        # #return redirect(url_for('public.index'))
        
    if not driver_profile:
        flash("Tu perfil de conductor no está completo.", "warning")
        return redirect(url_for('driver.profile_setup'))

    # 2️⃣ Estados activos
    active_statuses = [
        OrderStatus.ACCEPTED.value,
        OrderStatus.OUT_FOR_DELIVERY.value
    ]

    # 3️⃣ Consulta de pedidos asignados
    # query = (
        # db.select(Order)
        # .filter(
            # Order.driver_id == driver_profile.id,
            # Order.status.in_(active_statuses)
        # )
        # .options(
            # joinedload(Order.user).joinedload(User.customer_profile),
            # joinedload(Order.service),
            # joinedload(Order.items).joinedload(OrderItem.product),
            # joinedload(Order.items).joinedload(OrderItem.paquete_envio)
        # )
        # .order_by(Order.order_date.asc())
    # )
    # 3️⃣ Pedidos activos del driver
    orders = (
        db.session.execute(
            db.select(Order)
            .filter(
                Order.driver_id == driver_profile.id,
                Order.status.in_(active_statuses)
            )
            .options(
                joinedload(Order.user),
                joinedload(Order.service),
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.items).joinedload(OrderItem.paquete_envio)
            )
            .order_by(Order.order_date.asc())
        )
        .unique()
        .scalars()
        .all()
    )

    # result = db.session.execute(query)

    # # 🔑 Evita duplicados por JOIN con items
    # orders = result.unique().scalars().all()
    
    # Todos los pedidos para el motorizado
    # driver = current_user.driver

    active_order = driver_has_active_order(driver_profile.id)

    available_orders = []
    if driver_profile.saldo_cuenta > 0 and not active_order:
        available_orders = Order.query.filter(
            Order.status == OrderStatus.PENDING.value,
            Order.driver_id.is_(None)
        ).all()

    current_app.logger.warning(
        f"[DEBUG] driver={driver_profile.id} active_order={active_order}"
    )

    return render_template(
        'driver/dashboard.html',
        driver_profile=driver_profile,
        orders=orders,
        form = EmptyForm(),
        #accept_form=form,
        OrderStatus=OrderStatus,
        available_orders=available_orders,
        active_order=active_order
    )

@driver_bp.route("/notifications")
@login_required
@driver_required
#@role_required("driver")
def driver_notifications():
  
    driver = current_user.driver_profile

    if not driver or not driver.is_available:
        return jsonify({
            "has_new": False,
            "is_available": False
        })

    pending = Order.query.filter(
        Order.status == OrderStatus.PENDING.value,
        Order.driver_id.is_(None)
    ).count()

    return jsonify({
        "has_new": pending > 0,
        "count": pending,
        "is_available": True
    })


@driver_bp.route('/profile/setup', methods=['GET', 'POST'])
@driver_required
def profile_setup():
    driver_profile = db.session.execute(db.select(Driver).filter_by(user_id=current_user.id)).scalar_one_or_none()
    form = EmptyForm() # También se necesita aquí si la plantilla usa csrf_token() directamente
    
    if request.method == 'POST':
        if driver_profile:
            driver_profile.first_name = request.form['first_name']
            driver_profile.last_name = request.form['last_name']
            driver_profile.phone_number = request.form['phone_number'] 
            driver_profile.vehicle_type = request.form['vehicle_type']
            driver_profile.license_plate = request.form['license_plate']
            flash('Perfil actualizado exitosamente!', 'success')
        else:
            new_driver_profile = Driver(
                user_id=current_user.id,
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                phone_number=request.form['phone_number'],
                vehicle_type=request.form['vehicle_type'],
                license_plate=request.form['license_plate']
            )
            db.session.add(new_driver_profile)
            flash('Perfil creado exitosamente!', 'success')
            
        db.session.commit()
        return redirect(url_for('driver.dashboard'))
    
    return render_template('driver/profile_setup.html', driver_profile=driver_profile, form=form)


@driver_bp.route('/order/<int:order_id>/accept', methods=['POST'])
@login_required
@driver_required
def accept_order(order_id):

    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Error de seguridad.', 'danger')
        return redirect(url_for('driver.dashboard'))

    driver = db.session.execute(
        db.select(Driver).filter_by(user_id=current_user.id)
    ).scalar_one_or_none()

    if not driver:
        flash('Perfil de motorizado no encontrado.', 'danger')
        return redirect(url_for('driver.dashboard'))

    try:
        # 🔒 Lock SOLO del pedido
        order = db.session.execute(
            db.select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not order:
            flash('Pedido no encontrado.', 'danger')
            return redirect(url_for('driver.dashboard'))

        if order.driver_id is not None:
            flash('Este pedido ya fue tomado.', 'warning')
            return redirect(url_for('driver.dashboard'))

        # 🔒 Validar que el driver no tenga otro activo
        active_order = db.session.execute(
            db.select(Order)
            .where(
                Order.driver_id == driver.id,
                Order.status.in_([
                    OrderStatus.ACCEPTED.value,
                    OrderStatus.OUT_FOR_DELIVERY.value
                ])
            )
        ).scalar_one_or_none()

        if active_order:
            flash('Ya tienes un domicilio en curso.', 'warning')
            return redirect(url_for('driver.dashboard'))
            
        if not can_transition(order.status, OrderStatus.ACCEPTED.value):
            flash("Este pedido no puede ser aceptado en su estado actual.", "warning")
            return redirect(url_for("driver.dashboard"))

        # ✅ Asignar
        order.driver_id = driver.id
        order.status = OrderStatus.ACCEPTED.value
        order.fecha_asignacion = datetime.utcnow()

        db.session.commit()   # ← UN SOLO COMMIT

        flash(f'Has aceptado el pedido #{order.id}.', 'success')
        return redirect(url_for('driver.my_orders'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error crítico al aceptar pedido")
        flash("Error al aceptar el pedido.", "danger")
        return redirect(url_for('driver.dashboard'))


@driver_bp.route('/order/<int:order_id>/update_delivery_status', methods=['POST'])
@driver_required
def update_delivery_status(order_id):
    # Validar el token CSRF antes de procesar
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Error de seguridad. Recargue la página e intente de nuevo.', 'danger')
        return redirect(url_for('driver.dashboard'))

    driver_profile = db.session.execute(db.select(Driver).filter_by(user_id=current_user.id)).scalar_one_or_none()
    
    if not driver_profile:
        flash('Perfil de motorizado no encontrado.', 'danger')
        return redirect(url_for('driver.dashboard'))

    order = db.session.execute(
        db.select(Order)
        .filter_by(id=order_id, driver_id=driver_profile.id) # Asegura que el pedido le pertenece al motorizado
        .options(joinedload(Order.user), joinedload(Order.business)) # CORREGIDO AQUÍ: Usamos order.business
    ).scalar_one_or_none()

    if not order:
        flash('Pedido no encontrado o no te pertenece.', 'danger')
        return redirect(url_for('driver.dashboard'))

    new_status = request.form.get('new_status')
    special_message = request.form.get('special_message', '').strip() # Para mensajes especiales

    # Validar que el nuevo estado sea uno permitido para el motorizado
    if new_status not in [OrderStatus.OUT_FOR_DELIVERY.value, OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
        flash('Estado de pedido no válido para motorizado.', 'danger')
        return redirect(url_for('driver.dashboard'))

    # Lógica de estados para el motorizado:
    # Solo puede cambiar a 'En Camino', 'Entregado', o 'Cancelado'
    if new_status == OrderStatus.DELIVERED.value:
        order.fecha_entrega = datetime.utcnow()
        cobrar_comision_domicilio(order.id)
    
    if new_status == OrderStatus.CANCELLED.value:
        order.fecha_entrega = datetime.utcnow() # Registra la hora de cancelación
        # Aquí puedes añadir lógica para penalizaciones o reembolsos
        
    try:
        order.status = new_status
        
        # REGISTRO DEL CAMBIO DE ESTADO EN EL HISTORIAL
        # Asumiendo que HistorialEstadoPedido es una clase de modelo válida
        # history_entry = HistorialEstadoPedido(
        #     pedido_id=order.id,
        #     estado=new_status,
        #     usuario_cambio_id=current_user.id # El motorizado (usuario) que realizó el cambio
        # )
        # db.session.add(history_entry)

        db.session.commit()
        flash(f'Estado del pedido #{order.id} actualizado a "{new_status}"', 'success')
        
        status_messages = {
            "Aceptado": "Tu pedido fue aceptado por el conductor 🚴‍♂️",
            "En Camino": "Tu pedido está en camino 🛵",
            "Entregado": "Tu pedido fue entregado con éxito 📦"
        }

        if new_status in status_messages:
            notification = Notification(
                user_id=order.user_id,
                message=status_messages[new_status],
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
        
        notify(
            order.user_id,
            f"Tu pedido #{order.id} ahora está en estado: {new_status}"
        )

        # --- Notificaciones Email ---
        # Notificar al cliente sobre el cambio de estado
        if order.user and order.user.email:
            email_subject = f'Actualización de tu pedido #{order.id}: {new_status}'
            template_to_render = 'customer_order_status_update'
            
            # Si hay un mensaje especial, usarlo
            if special_message:
                email_subject = f'¡Importante! Actualización de tu pedido #{order.id}'
                template_to_render = 'customer_order_special_message' # Nueva plantilla para mensajes especiales
                try:
                    send_email(
                        order.user.email,
                        email_subject,
                        template_to_render,
                        order=order,
                        driver=driver_profile,
                        special_message=special_message
                    )
                    notification = Notification(
                        user_id=order.customer_id,
                        title="Actualización de tu pedido",
                        message=f"Tu pedido #{order.id} cambió de estado a: {order.delivery_status}",
                        is_read=False
                    )

                    db.session.add(notification)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.warning(
                        f"Email no enviado (bloqueado o timeout): {e}"
                    )    
        
        # Notificar al negocio sobre el cambio de estado
        if order.business and order.business.user and order.business.user.email: # Usamos order.business
            send_email(
                order.business.user.email, # Usamos order.business
                f'Actualización de pedido #{order.id}: {new_status} (Por Motorizado)',
                'business_order_status_update',
                order=order,
                driver=driver_profile
            )
        # ---------------------------

    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el estado del pedido: {str(e)}', 'danger')
        current_app.logger.error(f"Error al actualizar estado de pedido {order.id} por motorizado: {e}")

    return redirect(url_for('driver.dashboard'))



# 1. RUTA PARA VER PEDIDOS ASIGNADOS (CON RESTRICCIÓN DE SALDO)
@driver_bp.route('/my_orders')
@login_required
@driver_required
def my_orders():
    driver_profile = current_user.driver_profile
    form = ToggleAvailabilityForm()

    # SOLO estados cerrados reales (usando el value del Enum)
    estados_cerrados = [
        OrderStatus.DELIVERED.value,   # 'Entregado'
        OrderStatus.CANCELLED.value    # 'Cancelado'
    ]

    query = Order.query.filter(
        Order.driver_id == driver_profile.id,
        Order.status.in_(estados_cerrados)
    )

    # -------- FILTROS --------
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if status in estados_cerrados:
        query = query.filter(Order.status == status)

    if start_date:
        query = query.filter(Order.order_date >= datetime.strptime(start_date, "%Y-%m-%d"))

    if end_date:
        query = query.filter(Order.order_date <= datetime.strptime(end_date, "%Y-%m-%d"))

    orders = query.order_by(Order.order_date.desc()).all()
    
    # Restricción: Sin saldo, no hay pedidos
    if driver_profile.saldo_cuenta <= 0:
        flash('No tienes saldo suficiente en tu cuenta para aceptar pedidos. Por favor, recarga.', 'warning')
        #return render_template('driver/my_orders.html', orders=[], driver=driver_profile, form=form)

    # Alerta de saldo bajo
    if driver_profile.saldo_cuenta <= 500:
        flash('Alerta: Tu saldo es bajo. Recárgalo pronto para no dejar de recibir pedidos.', 'info')
        
    entregados_count = sum(1 for o in orders if o.status == OrderStatus.DELIVERED.value)
    cancelados_count = sum(1 for o in orders if o.status == OrderStatus.CANCELLED.value)
    total_ganado = sum(o.total_amount for o in orders if o.status == OrderStatus.DELIVERED.value)    

    
    return render_template('driver/my_orders.html', orders=orders, driver_profile=driver_profile, OrderStatus=OrderStatus, entregados_count=entregados_count, cancelados_count=cancelados_count,  form=form)

# 2. RUTA PARA CAMBIAR DISPONIBILIDAD (EL TOGGLE)
@driver_bp.route('/toggle_availability', methods=['POST'])
@login_required
@driver_required
def toggle_availability():
    driver_profile = current_user.driver_profile
    driver_profile.is_available = not driver_profile.is_available
    db.session.commit()
    
    if request.headers.get('X-Requested-With')== 'XMLHttpRequest':
        return jsonify({"is_available": driver_profile.is_available})
        
    flash (
        f"Estado cambiado a {'Disponible' if driver_profile.is_available else 'No disponible'}",
        "success"
    )
    
    return redirect(url_for('driver.dashboard')) # O a un dashboard de conductor

# 3. RUTA PARA RECARGAR SALDO (EJEMPLO SIMPLE)
@driver_bp.route('/recharge', methods=['GET', 'POST'])
@driver_required
def recharge_balance():
    # --- >>> AÑADIDO: Crear instancia del formulario <<< ---
    # Se necesita para el token CSRF en la plantilla.
    form = EmptyForm()
    if request.method == 'POST':
        amount_str = request.form.get('amount')
        try:
            #amount = Decimal(amount_str)
            
            amount= Decimal(str(amount_str))
            
            # Regla: Mínimo 10.000
            if amount < 10000:
                flash('La recarga mínima es de 10.000 pesos.', 'danger')
            else:
                # ...
                driver_profile.saldo_cuenta += amount
                create_transaction(
                    user_id=driver_profile.user_id,
                    amount=amount, # Positivo, es un crédito
                    trans_type=TransactionType.DRIVER_RECHARGE,
                    description=f"Recarga de saldo por ${amount:,.2f}"
                )
                db.session.commit()
                flash(f'Has recargado {amount:,.2f} pesos a tu cuenta. ¡Gracias!', 'success')
                return redirect(url_for('driver.my_orders'))
        except (ValueError, TypeError):
            flash('Por favor, introduce un monto válido.', 'danger')
            
    return render_template('driver/recharge_form.html',form=form)

# 4. LÓGICA PARA COBRAR COMISIÓN (ESTO ES UNA FUNCIÓN, NO UNA RUTA)
# Esta función la llamará el administrador o un proceso automático cuando un pedido se complete.
def cobrar_comision_domicilio(order_id):
    order = db.session.get(Order, order_id)
    if not order or not order.driver_id:
        print(f"Error: No se encontró el pedido {order_id} o no tiene conductor asignado.")
        return

    driver = db.session.get(Driver, order.driver_id)
    if not driver:
        print(f"Error: No se encontró el conductor con ID {order.driver_id}.")
        return

    comision = Decimal(str(order.costo_domicilio)) * Decimal('0.20')
    admin_user = db.session.execute(db.select(User).filter_by(role='admin')).scalar_one()

    # 1. Se le resta al conductor
    driver.saldo_cuenta -= comision

    # 2. Se crean las transacciones
    # Débito para el conductor
    create_transaction(
        user_id=driver.user_id,
        amount=-comision, # Negativo, es un débito
        trans_type=TransactionType.COMMISSION_PAYMENT,
        description=f"Pago de comisión del 20% por pedido #{order.id}",
        order_id=order.id
    )
    # Crédito para el admin
    create_transaction(
        user_id=admin_user.id,
        amount=comision, # Positivo, es una ganancia
        trans_type=TransactionType.COMMISSION_EARNING,
        description=f"Ganancia de comisión del 20% por pedido #{order.id}",
        order_id=order.id
    )
    # Aquí podrías registrar la transacción en otra tabla para llevar un historial
    print(f"Se descontó una comisión de {comision:,.2f} al conductor {driver.first_name} por el pedido {order.id}.")
    #db.session.commit()