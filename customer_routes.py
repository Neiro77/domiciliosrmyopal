# rm_domicilios_yopal/customer_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app 
from flask_login import login_required, current_user
from functools import wraps
from extensions import db # Importa db para interacciones con la DB
from models import User, Customer, Driver, Business, Product, Category, Order, OrderItem, PaymentMethod, Address, Service, OrderStatus, PaymentStatus, DetallesPaqueteEnvio, TransactionType, create_transaction, Notification # <-- Importa lo nuevo # Asegúrate de importar DetallesPaqueteEnvio # Importa los modelos necesarios
from forms import CheckoutForm, AddressForm, PackageForm, EmptyForm  # Importa los nuevos formularios # Importa los nuevos formularios
import json # Necesario para parsear el JSON del carrito (aunque no en checkout directamente ahora)
from sqlalchemy import exc # Para manejar excepciones de SQLAlchemy
from sqlalchemy.orm import joinedload # Importar joinedload para cargar relaciones
from sqlalchemy.sql import func # Para usar funciones de SQL como now()
from decimal import Decimal # Importar Decimal para manejar valores monetarios
from flask_mail import Message # Para construir mensajes de correo
from datetime import datetime, timedelta
from wtforms.validators import DataRequired, Optional

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

# --- Utilidades de Email (Para simplificar, se incluye aquí. En una app grande, sería un módulo separado) ---
def send_email(to_email, subject, template_name, **kwargs):
    try:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender:
            current_app.logger.error("MAIL_DEFAULT_SENDER no está configurado en app.py. No se puede enviar el email.")
            return

        msg = Message(subject, recipients=[to_email], sender=sender)
        msg.html = render_template(f'emails/{template_name}.html', **kwargs)
        mail.send(msg)
        current_app.logger.info(f"Email enviado a {to_email} con asunto: {subject}")
    except Exception as e:
        current_app.logger.error(f"Error al enviar email a {to_email}: {e}")
        # flash(f"Error al enviar notificación por email a {to_email}.", 'danger') # No flashear en el flujo normal


# Decorador para requerir rol de cliente
def customer_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'customer':
            flash('Acceso denegado. Solo para clientes.', 'danger')
            return redirect(url_for('public.login'))
        return f(*args, **kwargs)
    return decorated_function

@customer_bp.route('/dashboard')
@customer_required
def dashboard():
    """
    Muestra la nueva página de bienvenida para el cliente,
    presentando las opciones de servicio disponibles.
    """
    # Lógica para obtener el perfil del cliente
    customer_profile = db.session.execute(
        db.select(Customer).filter_by(user_id=current_user.id)
    ).scalar_one_or_none()

    # Si por alguna razón no tiene perfil, se crea uno básico para evitar errores.
    if customer_profile is None:
        flash('Tu perfil de cliente no ha sido configurado. Por favor, completa tus datos.', 'warning')
        customer_profile = Customer(first_name="Usuario", last_name="Nuevo", phone_number="N/A", user_id=current_user.id) 
        
    unread_notifications_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()    
    
    # Renderiza la nueva plantilla del dashboard
    return render_template('customer/dashboard.html', unread_notifications_count=unread_notifications_count, customer_profile=customer_profile)
# @customer_bp.route('/dashboard')
# @customer_required
# def dashboard():
    # # Lógica para obtener el perfil del cliente
    # customer_profile = db.session.execute(
        # db.select(Customer).filter_by(user_id=current_user.id)
    # ).scalar_one_or_none()

    # if customer_profile is None:
        # flash('Tu perfil de cliente no ha sido configurado. Por favor, completa tus datos.', 'warning')
        # customer_profile = Customer(first_name="Usuario", last_name="Nuevo", phone_number="N/A", user_id=current_user.id) 
    
    # # Redirigir al cliente a la lista de negocios directamente desde el dashboard
    # return redirect(url_for('customer.list_businesses'))

@customer_bp.route('/businesses')
@customer_required
def list_businesses():
    # Obtener todos los negocios activos y ordenarlos por nombre
    businesses = db.session.execute(
        db.select(Business)
        .join(User) # Unir con la tabla de usuarios
        .filter(User.is_active == True) # Filtrar solo usuarios activos
        .order_by(Business.name)
    ).scalars().all()
    
    return render_template('customer/business_list.html', businesses=businesses)

@customer_bp.route('/business/<int:business_id>')
@customer_required
def view_business(business_id):
    # Obtener el negocio específico
    business = db.session.execute(
        db.select(Business)
        .join(User) # Unir con la tabla de usuarios
        .filter(Business.id == business_id, User.is_active == True) # Asegurarse de que el negocio esté activo
    ).scalar_one_or_none()

    if not business:
        flash('Negocio no encontrado o no activo.', 'danger')
        return redirect(url_for('customer.list_businesses'))

    # Obtener los productos de ese negocio
    products = db.session.execute(
        db.select(Product)
        .filter_by(business_id=business.id, is_available=True) # Solo productos disponibles
        .order_by(Product.name)
    ).scalars().all()

    # Obtener las categorías de comida para filtrar o mostrar
    categories = db.session.execute(
        db.select(Category)
        .join(Product, Category.id == Product.category_id)
        .filter(Product.business_id == business.id, Product.is_available == True)
        .distinct()
        .order_by(Category.name)
    ).scalars().all()

    return render_template('customer/business_detail.html', business=business, products=products, categories=categories)

# --- Rutas para el Carrito de Compras (AJAX Habilitado) ---

@customer_bp.route('/cart')
@customer_required
def view_cart():
    # Obtener el carrito de la sesión
    carrito = session.get('carrito', {})
    products_in_cart = []
    subtotal = Decimal('0.00')
    business = None

    if not carrito:
        flash('Tu carrito está vacío.', 'info')
        return render_template('customer/cart.html', products_in_cart=[], subtotal=subtotal, business=None)

    business_id_in_cart = None
    for prod_id_str, quantity in carrito.items():
        product = db.session.get(Product, int(prod_id_str))
        if product:
            product.quantity_in_cart = quantity
            products_in_cart.append(product)
            subtotal += Decimal(str(product.price)) * Decimal(quantity) # Convertir a Decimal
            if business_id_in_cart is None:
                business_id_in_cart = product.business_id
            elif business_id_in_cart != product.business_id:
                # Esto debería ser prevenido por add_to_cart, pero es un fallback
                flash('Tu carrito contiene productos de múltiples negocios, lo cual no está permitido. Por favor, vacía tu carrito y vuelve a empezar.', 'danger')
                session.pop('carrito', None)
                session.modified = True
                return redirect(url_for('customer.list_businesses'))
        else:
            del carrito[prod_id_str]
            session['carrito'] = carrito
            session.modified = True
            flash(f'Un producto con ID {prod_id_str} no se encontró y fue eliminado del carrito.', 'warning')

    if business_id_in_cart:
        business = db.session.get(Business, business_id_in_cart)
        if not business:
            flash('El negocio de los productos en tu carrito no se encontró.', 'danger')
            session.pop('carrito', None)
            session.modified = True
            return redirect(url_for('customer.list_businesses'))
            
    return render_template('customer/cart.html', products_in_cart=products_in_cart, subtotal=subtotal, business=business)
    
    
# @customer_bp.route('/cart')
# @customer_required
# def view_cart():
    # # This route simply renders the cart.html. The cart data itself is handled by Alpine.js
    # # on the client side. When proceeding to checkout, we'll need to send this data.
    # return render_template('customer/cart.html')

@customer_bp.route('/add_to_cart', methods=['POST'])
@customer_required
def add_to_cart():
    # Acepta datos de formulario (form-urlencoded) o JSON.
    # Si viene de FormData en JS, será request.form
    product_id = request.form.get('product_id', type=int)
    quantity_to_add = request.form.get('quantity', type=int)

    if not product_id or not quantity_to_add or quantity_to_add <= 0:
        return jsonify({'error': 'Cantidad o producto inválido.'}), 400

    product = db.session.get(Product, product_id)
    if not product or not product.is_available:
        return jsonify({'error': 'Producto no disponible.'}), 404
    
    carrito = session.get('carrito', {})
    
    # Validar si el carrito ya tiene productos de otro negocio
    if carrito:
        first_product_id_in_cart = next(iter(carrito))
        first_product_in_cart_obj = db.session.get(Product, int(first_product_id_in_cart))
        if first_product_in_cart_obj and first_product_in_cart_obj.business_id != product.business_id:
            # Si se intentó añadir de otro negocio, limpiar el carrito actual en sesión
            # Esto se manejará en el frontend con el `confirm` antes de llamar a esta ruta
            # Si llega aquí, significa que el usuario aceptó limpiar el carrito.
            session['carrito'] = {}
            carrito = {}
            # flash('Tu carrito ha sido vaciado porque agregaste un producto de un negocio diferente.', 'warning') # Flash message not needed for AJAX
    
    str_product_id = str(product_id)
    
    # Actualizar la cantidad en el carrito de la sesión
    current_quantity_in_cart = carrito.get(str_product_id, 0)
    new_total_quantity = current_quantity_in_cart + quantity_to_add

    # Aquí podrías añadir una comprobación de stock si tu modelo Product tiene un campo 'quantity' para stock
    # if hasattr(product, 'quantity') and product.quantity < new_total_quantity:
    #    return jsonify({'error': f'Solo hay {product.quantity} unidades de "{product.name}" disponibles.'}), 400


    carrito[str_product_id] = new_total_quantity
    session['carrito'] = carrito
    session.modified = True

    return jsonify({'message': f'"{product.name}" añadido al carrito.', 'item_count': len(carrito), 'total_quantity': new_total_quantity}), 200


@customer_bp.route('/update_cart', methods=['POST'])
@customer_required
def update_cart():
    product_id = request.form.get('product_id', type=int)
    new_quantity = request.form.get('quantity', type=int) # Esta es la cantidad TOTAL deseada

    carrito = session.get('carrito', {})
    str_product_id = str(product_id)

    if str_product_id not in carrito:
        return jsonify({'error': 'El producto no está en tu carrito.'}), 404

    product = db.session.get(Product, product_id)
    if not product:
        # Si el producto no existe en DB, lo eliminamos del carrito de sesión
        del carrito[str_product_id]
        session['carrito'] = carrito
        session.modified = True
        return jsonify({'error': 'Producto no encontrado y eliminado del carrito.'}), 404

    if new_quantity <= 0:
        del carrito[str_product_id]
        message = f'"{product.name}" eliminado del carrito.'
    # Si tienes un campo 'quantity' para stock en el modelo Product, descomenta y usa esta lógica:
    # elif hasattr(product, 'quantity') and product.quantity < new_quantity:
    #     message = f'Solo hay {product.quantity} unidades de "{product.name}" disponibles. Cantidad ajustada.'
    #     carrito[str_product_id] = product.quantity # Ajustar a stock disponible
    else:
        carrito[str_product_id] = new_quantity
        message = f'Cantidad de "{product.name}" actualizada a {new_quantity}.'

    session['carrito'] = carrito
    session.modified = True
    return jsonify({'message': message, 'item_count': len(carrito), 'new_quantity': carrito.get(str_product_id, 0)}), 200


@customer_bp.route('/clear_cart', methods=['POST'])
@customer_required
def clear_cart():
    session.pop('carrito', None)
    session.modified = True
    return jsonify({'message': 'Carrito vaciado en el servidor.'}), 200


# --- Nueva Ruta para Crear Pedidos de Paquetes ---
@customer_bp.route('/create_package', methods=['GET', 'POST'])
@customer_required
def create_package():

    form = PackageForm()

    if form.validate_on_submit():
        try:
            # 🧠 VALOR FIJO DEL SERVICIO (NO ES PRECIO DE PRODUCTO)
            PRECIO_ENVIO_RAPIDO = 7000.0

            # 📦 Crear y guardar el detalle del paquete (SIN COBRAR AQUÍ)
            new_package_detail = DetallesPaqueteEnvio(
                descripcion=form.descripcion.data,
                nombre_quien_recibe=form.nombre_quien_recibe.data,
                telefono_quien_recibe=form.telefono_quien_recibe.data,
                precio_calculado=0  # 🔑 IMPORTANTE: NO es el costo del servicio
            )

            db.session.add(new_package_detail)
            db.session.commit()  # Necesario para obtener el ID

            flash(
                'Paquete listo para envío. Revisa los detalles y confirma tu pedido.',
                'success'
            )

            # --- 🛒 LÓGICA CORRECTA DEL CARRITO ---
            # El paquete NO tiene precio (subtotal = 0)
            session['cart_items'] = [{
                'type': 'package',
                'id': new_package_detail.id,
                'name': 'Envío rápido de paquete',
                'price': 0,          # ✅ Subtotal = 0
                'quantity': 1
            }]

            # El domicilio se maneja como SERVICIO, no como producto
            session['shipping_cost'] = PRECIO_ENVIO_RAPIDO  # 👈 clave
            session['cart_business_id'] = None
            session['cart_business_name'] = 'Servicio de Paquetería'
            session['service_type'] = 'envio_rapido'

            session.modified = True

            return redirect(url_for('customer.checkout'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear paquete: {e}")
            flash(
                f'Ocurrió un error al crear el paquete: {str(e)}',
                'danger'
            )

    if not form.validate_on_submit():
        flash('Por favor completa todos los campos requeridos.', 'danger')

    return render_template(
        'customer/create_package.html',
        form=form
    )

@customer_bp.route('/update_session_cart', methods=['POST'])
@customer_required
def update_session_cart():
    try:
        data = request.get_json()
        cart_items = data.get('cart_items', [])
        business_id = data.get('business_id')
        business_name = data.get('business_name')

        session['cart_items'] = cart_items
        session['cart_business_id'] = business_id
        session['cart_business_name'] = business_name
        
        # Explicitly mark the session as modified
        session.modified = True 
        
        return jsonify({'success': True, 'message': 'Carrito actualizado en sesión.'})
    except Exception as e:
        current_app.logger.error(f"Error updating session cart: {e}")
        return jsonify({'success': False, 'message': 'Error interno al actualizar el carrito.'}), 500

# --- Rutas para Checkout y Pedido ---

# --- Ruta de Checkout (CORREGIDA) ---
@customer_bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    cart_items_data = session.get('cart_items', [])
    if not cart_items_data:
        flash('Tu carrito está vacío.', 'info')
        return redirect(url_for('customer.list_businesses'))

    business_id = session.get('cart_business_id')
    business = db.session.get(Business, int(business_id)) if business_id else None
    
    customer_profile = db.session.execute(
        db.select(Customer).filter_by(user_id=current_user.id).options(joinedload(Customer.addresses))
    #).scalar_one_or_none()
    ).scalars().unique().one_or_none() # <--- CAMBIO CLAVE AQUÍ: .scalars().unique().one_or_none()
    
    if not customer_profile:
        flash('Perfil de cliente no encontrado.', 'danger')
        return redirect(url_for('public.home'))

    item_type = cart_items_data[0].get('type', 'product')
    form = CheckoutForm()

    # --- CORRECCIÓN 1: Poblar las opciones del formulario ANTES de cualquier validación ---
    # Esto soluciona el error 'TypeError: Choices cannot be None.'
    address_choices = [(addr.id, addr.full_address) for addr in customer_profile.addresses]
    form.address_id.choices = address_choices
    form.pickup_address_id.choices = address_choices # También poblamos las opciones de recogida
    
    payment_methods = db.session.execute(db.select(PaymentMethod).filter_by(is_active=True)).scalars().all()
    form.payment_method_id.choices = [(pm.id, pm.name) for pm in payment_methods]

    # Lógica condicional para hacer obligatorio el campo de recogida si es un paquete
    if item_type == 'package':
        form.pickup_address_id.validators = [DataRequired(message="Debes seleccionar una dirección de recogida.")]

    if form.validate_on_submit():
        try:
            # --- CORRECCIÓN 2: Usar el Modelo 'Address' directamente ---
            # Esto soluciona el error 'UnboundLocalError'
            delivery_address_obj = db.session.get(Address, int(form.address_id.data))
            
            # ... (código para calcular totales y obtener el servicio) ...
            # Esta parte debe estar completa en tu código
            cart_total = sum(
                Decimal(str(item.get('price', 0))) * int(item.get('quantity', 1))
                for item in cart_items_data
            )

            # 🔑 COSTO DOMICILIO UNIFICADO
            if item_type == 'package':
                costo_domicilio = Decimal(str(session.get('shipping_cost', 0)))
            else:
                costo_domicilio = Decimal(str(business.delivery_fee)) if business and business.delivery_fee else Decimal('0.00')

            total_final = cart_total + costo_domicilio
            service_name = 'comidas' if item_type == 'product' else 'paquetes'
            service_obj = db.session.execute(db.select(Service).filter_by(name=service_name)).scalar_one_or_none()
            payment_method_obj = db.session.get(PaymentMethod, int(form.payment_method_id.data))
            
            new_order = Order(
                user_id=current_user.id,
                business_id=business.id if business else None,
                servicio_id=service_obj.id,
                total_amount=float(total_final),
                costo_domicilio=float(costo_domicilio),
                status=OrderStatus.PENDING.value,
                payment_status=PaymentStatus.PENDING.value,
                payment_method_id=payment_method_obj.id,
                delivery_address=delivery_address_obj.full_address,
                direccion_entrega_id=delivery_address_obj.id,
                notes=form.notes.data
            )

            if item_type == 'package':
                pickup_address_obj = db.session.get(Address, int(form.pickup_address_id.data))
                new_order.pickup_address = pickup_address_obj.full_address
                new_order.direccion_recogida_id = pickup_address_obj.id

                # 🔒 PRECIO BASE FIJO DEL SERVICIO
                SHIPPING_COST = Decimal('7000.00')

                new_order.subtotal = 0
                new_order.costo_domicilio = float(SHIPPING_COST)
                new_order.total_amount = float(SHIPPING_COST)
            
            db.session.add(new_order)
            db.session.flush()

            # ... (resto de la lógica para guardar OrderItems y hacer commit) ...
            # Esta parte debe estar completa en tu código
            if item_type == 'product':
                product_ids = [item['productId'] for item in cart_items_data if item['type'] == 'product']
                products = db.session.execute(db.select(Product).filter(Product.id.in_(product_ids))).scalars().all()
                product_map = {p.id: p for p in products}
                for item_data in cart_items_data:
                    product = product_map.get(item_data['productId'])
                    if product:
                        order_item = OrderItem(order_id=new_order.id, tipo_item='producto_comida', product_id=product.id, quantity=item_data['quantity'], price_at_order=product.price)
                        db.session.add(order_item)
            elif item_type == 'package':
                for item_data in cart_items_data:
                    package_details = db.session.get(DetallesPaqueteEnvio, item_data['id'])
                    if package_details:
                        order_item = OrderItem(order_id=new_order.id, tipo_item='paquete_envio', paquete_envio_id=package_details.id, quantity=1, price_at_order=package_details.precio_calculado)
                        db.session.add(order_item)

            db.session.commit()
            
            session.pop('cart_items', None)
            session.pop('cart_business_id', None)
            session.pop('cart_business_name', None)
            session.modified = True

            flash(f'¡Tu pedido #{new_order.id} ha sido realizado con éxito!', 'success')
            return redirect(url_for('customer.order_success', order_id=new_order.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error en checkout: {e}", exc_info=True)
            flash('Ocurrió un error inesperado al procesar tu pedido.', 'danger')
            return redirect(url_for('customer.checkout'))
            
    # Lógica para la solicitud GET
    cart_total = Decimal('0.00')

    if item_type == 'product':
        cart_total = sum(
            Decimal(str(item.get('price', item.get('productPrice', 0))))
            * int(item.get('quantity', 1))
            for item in cart_items_data
        )

    costo_domicilio = (
        Decimal('7000.00') if item_type == 'package'
        else Decimal(str(business.delivery_fee)) if business
        else Decimal('0.00')
    )

    total_final = cart_total + costo_domicilio
    
    return render_template('customer/checkout.html', 
                           form=form, 
                           cart_items=cart_items_data, 
                           cart_total=cart_total, 
                           business=business,
                           costo_domicilio=costo_domicilio,
                           total_final=total_final,
                           item_type=item_type)                           
                           
@customer_bp.route('/order_success/<int:order_id>')
@customer_required
def order_success(order_id):
    order_details = db.session.execute(
        db.select(Order)
        .filter_by(id=order_id, user_id=current_user.id)
        .options(
            joinedload(Order.business), 
            joinedload(Order.payment_method),
            joinedload(Order.delivery_address_obj), 
            joinedload(Order.items).joinedload(OrderItem.product), # Para productos de comida
            joinedload(Order.items).joinedload(OrderItem.paquete_envio) # Para detalles de paquete
        )
    ).scalars().unique().one_or_none() 

    if not order_details:
        flash('Pedido no encontrado o no tienes permiso para verlo.', 'danger')
        return redirect(url_for('customer.dashboard'))
    return render_template('customer/order_success.html', order=order_details)

# --- Rutas para Gestión de Direcciones ---

@customer_bp.route('/addresses', methods=['GET', 'POST'])
@customer_required
def manage_addresses():
    customer_profile = db.session.execute(db.select(Customer).filter_by(user_id=current_user.id)).scalar_one_or_none()
    if not customer_profile:
        flash('Completa tu perfil de cliente para gestionar direcciones.', 'warning')
        return redirect(url_for('customer.dashboard'))

    form = AddressForm()
    if form.validate_on_submit():
        new_address = Address(
            customer_id=customer_profile.id,
            address=form.address.data,
            alias=form.alias.data,
            is_principal=(form.is_principal.data == 'True'),
            latitud=float(form.latitud.data) if form.latitud.data else None,
            longitud=float(form.longitud.data) if form.longitud.data else None
        )
        db.session.add(new_address)
        db.session.commit()
        flash('Dirección añadida exitosamente!', 'success')
        return redirect(url_for('customer.manage_addresses'))

    user_addresses = db.session.execute(db.select(Address).filter_by(customer_id=customer_profile.id)).scalars().all()
    return render_template('customer/addresses.html', form=form, addresses=user_addresses)

@customer_bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@customer_required
def delete_address(address_id):
    address_to_delete = db.session.get(Address, address_id)
    if address_to_delete and address_to_delete.customer.user_id == current_user.id:
        db.session.delete(address_to_delete)
        db.session.commit()
        flash('Dirección eliminada.', 'info')
    else:
        flash('Dirección no encontrada o no tienes permiso para eliminarla.', 'danger')
    return redirect(url_for('customer.manage_addresses'))

@customer_bp.route('/addresses/<int:address_id>/set_principal', methods=['POST'])
@customer_required
def set_principal_address(address_id):
    customer_profile = db.session.execute(db.select(Customer).filter_by(user_id=current_user.id)).scalar_one_or_none()
    if not customer_profile:
        flash('Error al establecer dirección principal.', 'danger')
        return redirect(url_for('customer.manage_addresses'))

    # Desactivar todas las direcciones principales del cliente
    db.session.execute(db.update(Address).filter_by(customer_id=customer_profile.id, is_principal=True).values(is_principal=False))
    
    # Establecer la nueva dirección como principal
    new_principal = db.session.get(Address, address_id)
    if new_principal and new_principal.customer_id == customer_profile.id:
        new_principal.is_principal = True
        db.session.commit()
        flash('Dirección principal actualizada.', 'success')
    else:
        flash('Dirección no encontrada o no pertenece a tu cuenta.', 'danger')
        db.session.rollback()
    return redirect(url_for('customer.manage_addresses'))

# --- Nueva ruta para ver todos los pedidos del cliente ---
# --- Nueva ruta para ver todos los pedidos del cliente ---
# --- Ruta para ver todos los pedidos del cliente (CORREGIDA) ---

# --- Ruta para ver todos los pedidos del cliente (CORREGIDA) ---
# @customer_bp.route('/my_orders')
# @customer_required
# def my_orders():
    # """
    # Muestra todos los pedidos realizados por el cliente actual.
    # La consulta se simplificó para cargar solo los datos necesarios para la plantilla.
    # """
    # orders = db.session.execute(
        # db.select(Order)
        # .filter_by(user_id=current_user.id)
        # .options(
            # # Cargar eficientemente las relaciones que SÍ se usan en la plantilla
            # joinedload(Order.business),
            # joinedload(Order.payment_method),
            # joinedload(Order.service),
            # joinedload(Order.items).joinedload(OrderItem.product),
            # joinedload(Order.items).joinedload(OrderItem.paquete_envio)
            # # --- LÍNEA PROBLEMÁTICA ELIMINADA ---
            # # Se eliminó la línea que cargaba 'Order.history' porque causaba un error
            # # y la plantilla 'my_orders.html' no utiliza esta información.
        # )
        # .order_by(Order.order_date.desc())
    # ).scalars().unique().all()
    
    # return render_template('customer/my_orders.html', orders=orders)



# --- Ruta para ver todos los pedidos del cliente (VERSIÓN ACTUALIZADA) ---
# --- Ruta para ver todos los pedidos del cliente (VERSIÓN CORREGIDA) ---
@customer_bp.route('/my_orders')
@customer_required
def my_orders():
    """
    Muestra todos los pedidos realizados por el cliente actual.
    """
    customer_profile = db.session.execute(
        db.select(Customer).filter_by(user_id=current_user.id)
    ).scalar_one_or_none()

    if not customer_profile:
        flash('No se pudo encontrar tu perfil de cliente.', 'danger')
        return redirect(url_for('public.home'))

    # --- >>> LA SOLUCIÓN: Añadir .unique() <<< ---
    # Primero ejecutamos la consulta y luego aplicamos .unique() al resultado.
    result = db.session.execute(
        db.select(Order)
        .filter_by(user_id=current_user.id)
        .options(
            joinedload(Order.business),
            joinedload(Order.payment_method),
            joinedload(Order.service),
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.items).joinedload(OrderItem.paquete_envio)
        )
        .order_by(Order.order_date.desc())
    )
    
    # Aplicamos .unique() para eliminar duplicados de la consulta JOIN
    orders = result.unique().scalars().all()
    
    form = EmptyForm()

    return render_template(
        'customer/my_orders.html', 
        orders=orders, 
        customer=customer_profile,
        form=form
    )

# --- RUTA PARA CANCELAR PEDIDOS (LÓGICA DE PENALIZACIÓN DEFINITIVA) ---
@customer_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
@customer_required
def cancel_order(order_id):
    order = db.session.get(Order, order_id)

    if not order or order.user_id != current_user.id:
        flash('Pedido no encontrado o no autorizado para esta acción.', 'danger')
        return redirect(url_for('customer.my_orders'))

    # --- LÓGICA DE ESTADO MEJORADA ---
    # La única condición que impide cancelar es que el pedido ya haya sido entregado.
    if order.status == OrderStatus.DELIVERED.value:
        flash(f'No puedes cancelar un pedido que ya fue entregado.', 'warning')
        return redirect(url_for('customer.my_orders'))
        
    # También prevenimos cancelar un pedido ya cancelado.
    if order.status == OrderStatus.CANCELLED.value:
        flash('Este pedido ya se encuentra cancelado.', 'info')
        return redirect(url_for('customer.my_orders'))

    # Regla de tiempo: 5 minutos desde la creación del pedido
    cinco_minutos_despues = order.order_date + timedelta(minutes=5)

    try:
        # Siempre se actualiza el estado a Cancelado
        order.status = OrderStatus.CANCELLED.value

        if datetime.utcnow() <= cinco_minutos_despues:
            # --- CASO 1: Cancelación gratuita dentro de los 5 minutos ---
            flash(f'El pedido #{order.id} ha sido cancelado sin costo.', 'success')
        else:
            # --- CASO 2: Cancelación tardía con penalización ---
            
            # --- LÓGICA DE PENALIZACIÓN MEJORADA ---
            # Verificamos si el administrador ya asignó un costo de domicilio.
            if order.costo_domicilio and order.costo_domicilio > 0:
                # Si hay costo, la penalización es el 50% de ese valor.
                penalizacion_total = Decimal(order.costo_domicilio)
                admin_share = penalizacion_total * Decimal('0.50')
                driver_share = penalizacion_total * Decimal('0.50')
                admin_user = db.session.execute(db.select(User).filter_by(role='admin')).scalar_one()

                if order.driver_id:
                    driver = db.session.get(Driver, order.driver_id)
                    if driver:
                        driver.saldo_cuenta += driver_share
                        # Transacción para el conductor
                        create_transaction(driver.user_id, driver_share, TransactionType.CANCELLATION_PENALTY_DRIVER, f"Compensación por cancelación de pedido #{order.id}", order.id)
                        # Transacción para el admin
                        create_transaction(admin_user.id, admin_share, TransactionType.CANCELLATION_PENALTY_ADMIN, f"Ganancia por cancelación de pedido #{order.id}", order.id)
                else:
                    # Transacción completa para el admin
                    create_transaction(admin_user.id, penalizacion_total, TransactionType.CANCELLATION_PENALTY_ADMIN, f"Ganancia por cancelación (sin conductor) de pedido #{order.id}", order.id)

                db.session.commit()
            else:
                # # Si no hay costo asignado, se aplica una penalización fija.
                # # Esto evita que la cancelación sea gratis si el admin no ha actuado.
                # # PUEDES AJUSTAR ESTE VALOR FIJO.
                admin_user = db.session.execute(db.select(User).filter_by(role='admin')).scalar_one()
                penalizacion_total = Decimal('2000.00') 
                create_transaction(admin_user.id, penalizacion_total, TransactionType.CANCELLATION_PENALTY_ADMIN, f"Ganancia por cancelación sin conductor, pedido #{order.id}", order.id)
            
            # # Añadimos la penalización a la deuda del cliente
            customer_profile = current_user.customer_profile
            if customer_profile:
                customer_profile.deuda_cancelacion += penalizacion_total
            
            flash(f'Pedido #{order.id} cancelado. Se ha añadido un cargo de ${penalizacion_total:,.2f} a tu cuenta por cancelación tardía, sin conductor', 'warning')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al cancelar pedido {order_id}: {e}")
        flash('Ocurrió un error al intentar cancelar el pedido.', 'danger')

    return redirect(url_for('customer.my_orders'))
    
@customer_bp.route("/customer/notifications")
@customer_required
def notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()

    return jsonify([
        {
            "id": n.id,
            "message": n.message,
            "created_at": n.created_at.isoformat()
        } for n in notifications
    ])    
    




