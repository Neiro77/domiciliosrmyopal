from flask import Blueprint, render_template, redirect, url_for,  flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from extensions import db # Importa db para futuras interacciones con la DB
from models import User, Business, Order, OrderItem, Product, OrderStatus, Category, HistorialEstadoPedido, Driver # Importa los modelos necesarios y OrderStatus Enum
from functools import wraps # <--- ¡IMPORTA ESTO!
import re # Para slugify
from sqlalchemy.orm import joinedload # Importa joinedload si se utiliza en alguna parte
from forms import EmptyForm # <--- Importa el nuevo EmptyForm
from sqlalchemy.sql import func # Para usar funciones de SQL como now()


business_bp = Blueprint('business', __name__, url_prefix='/business')

# Un decorador para asegurar que solo los negocios puedan acceder a ciertas rutas
def business_required(f):
    @wraps(f) # <--- ¡AÑADE ESTA LÍNEA!
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'business':
            flash('Acceso denegado. Solo para negocios.', 'danger')
            return redirect(url_for('public.login'))
        return f(*args, **kwargs)
    return decorated_function

@business_bp.route('/dashboard')
@business_required
def dashboard():
    # Instantiate EmptyForm here so it's always available
    form = EmptyForm() # <--- Instancia el formulario vacío aquí

    business_profile = db.session.execute(
        db.select(Business).filter_by(user_id=current_user.id)
    ).scalar_one_or_none()

    if business_profile is None:
        flash('Tu perfil de negocio no ha sido configurado. Por favor, completa tus datos.', 'warning')
        # If business_profile is None, we still need to pass a form.
        return render_template('business/dashboard.html', 
                               business_profile=Business(name="Mi Negocio", user_id=current_user.id), 
                               orders=[], 
                               order_statuses=[],
                               form=form) # Pass the form even if profile is empty
    
    # Obtener los pedidos para este negocio, ordenados por fecha de pedido descendente
    # Cargamos las relaciones de usuario y ítems del pedido para mostrar en la plantilla
    orders = db.session.execute(
        db.select(Order)
        .filter_by(business_id=business_profile.id)
        .options(
            joinedload(Order.user), # Carga el usuario (cliente) que hizo el pedido
            joinedload(Order.items).joinedload(OrderItem.product) # Carga los ítems y sus productos
        )
        .order_by(Order.order_date.desc())
    ).unique().scalars().all()

    # Define los posibles estados a los que un negocio puede cambiar un pedido
    # Nota: Los estados 'En Camino' y 'Entregado' típicamente serían actualizados por el motorizado.
    # Aquí se incluyen para una visualización completa, pero la lógica de quién puede cambiar qué estado
    # debe ser más granular en una aplicación de producción.
    available_statuses = [
        #OrderStatus.PENDING.value,
        #OrderStatus.ACCEPTED.value,
        OrderStatus.PREPARING.value,
        #OrderStatus.OUT_FOR_DELIVERY.value,
        #OrderStatus.DELIVERED.value,
        OrderStatus.CANCELLED.value
    ]

    return render_template('business/dashboard.html', 
                           business_profile=business_profile, 
                           orders=orders,
                           order_statuses=available_statuses,
                           form=form) # Pass the form here as well

                           
                           
@business_bp.route('/order/<int:order_id>/update_status', methods=['POST'])
@business_required
def update_order_status(order_id):
    
    business_profile = db.session.execute(db.select(Business).filter_by(user_id=current_user.id)).scalar_one_or_none()
    
    if not business_profile:
        flash('Perfil de negocio no encontrado.', 'danger')
        return redirect(url_for('business.dashboard'))

    order = db.session.get(Order, order_id)
    
    # 🔒 BUSINESS NO MANDA SI YA HAY DRIVER, SI YA TIENE DRIVER, BUSINESS NO PUEDE CAMBIAR ESTADO
    if order.driver_id is not None and order.status != OrderStatus.PENDING.value:
        flash(
            "El pedido ya está en curso y no puede ser modificado.",
            "warning"
        )
        return redirect(url_for('business.dashboard'))

    # Validar que el pedido pertenezca al negocio actual
    if not order or order.business_id != business_profile.id:
        flash('Pedido no encontrado o no tienes permiso para modificarlo.', 'danger')
        return redirect(url_for('business.dashboard'))

    new_status = request.form.get('new_status')

    # Validar que el nuevo estado sea uno permitido y válido según el Enum
    if new_status not in [status.value for status in OrderStatus]:
        flash('Estado de pedido no válido.', 'danger')
        return redirect(url_for('business.dashboard'))
    
    # Lógica para cambiar el estado
    try:
               
        allowed_status_for_business = [
            OrderStatus.PREPARING.value,
            OrderStatus.CANCELLED.value
        ]

        if new_status not in allowed_status_for_business:
            flash("No autorizado para cambiar a ese estado", "danger")
            return redirect(url_for('business.dashboard'))

        order.status = new_status
        db.session.commit()
        
        # REGISTRO DEL ESTADO EN EL HISTORIAL
        history_entry = HistorialEstadoPedido(
            pedido_id=order.id,
            estado=new_status,
            usuario_cambio_id=current_user.id # El negocio (usuario) que realizó el cambio
        )
        db.session.add(history_entry)
        
        db.session.commit()
        flash(f'Estado del pedido #{order.id} actualizado a "{new_status}"', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el estado del pedido: {str(e)}', 'danger')
        current_app.logger.error(f"Error al actualizar estado de pedido {order.id}: {e}")

    return redirect(url_for('business.dashboard'))

# Puedes añadir más rutas de negocio aquí:
# @business_bp.route('/products')
# @business_bp.route('/settings')



# Ejemplo de ruta para configurar el perfil del negocio
@business_bp.route('/profile/setup', methods=['GET', 'POST'])
@business_required
def profile_setup():
    _db = current_app.extensions['sqlalchemy']
    business_profile = _db.session.execute(_db.select(Business).filter_by(user_id=current_user.id)).scalar_one_or_none()

    # Aquí iría un formulario para que el negocio ingrese sus datos
    # (ej. BusinessProfileForm, etc.)
    # Por ahora, un placeholder:
    if request.method == 'POST':
        # Procesar datos del formulario y guardarlos en business_profile o crear uno nuevo
        if business_profile:
            # Actualizar datos
            business_profile.name = request.form['name']
            business_profile.address = request.form['address']
            business_profile.phone_number = request.form['phone_number'] # Asegúrate de que el nombre del campo HTML sea 'phone_number'
            business_profile.description = request.form.get('description', '') # Usar .get para campos opcionales
            # No actualizamos el slug aquí, ya que se genera una vez.
            flash('Perfil actualizado exitosamente!', 'success')
        else:
            
            # Esto no debería ocurrir si el perfil se crea al registrarse, pero por si acaso
            # Generar slug para el nuevo negocio
            def slugify(text):
                text = text.lower()
                text = re.sub(r'[^\w\s-]', '', text)
                text = re.sub(r'[\s_-]+', '-', text)
                text = re.sub(r'^-+|-+$', '', text)
                return text

            business_slug = slugify(request.form['name'])
            counter = 0
            
            while True:
                if counter == 0:
                    current_slug = business_slug
                else:
                    current_slug = f"{business_slug}-{counter}"
                
                existing_business = db.session.execute(db.select(Business).filter_by(slug=current_slug)).scalar_one_or_none()
                if not existing_business:
                    break
                counter += 1
                
            # Crear nuevo perfil
            new_business_profile = Business(
                user_id=current_user.id,
                name=request.form['name'],
                address=request.form['address'],
                phone_number=request.form['phone_number'],
                description=request.form.get('description', ''),
                slug=current_slug
            )
            db.session.add(new_business_profile)
            flash('Perfil creado exitosamente!', 'success')
            
        db.session.commit()
        return redirect(url_for('business.dashboard'))
    
    return render_template('business/profile_setup.html', business_profile=business_profile)


# Puedes añadir más rutas de negocio aquí:
# @business_bp.route('/products')
# @business_bp.route('/orders')
# @business_bp.route('/settings')


# Puedes añadir más rutas aquí:
# @business_bp.route('/menu')
# @business_required
# def manage_menu():
#     # Lógica para que el negocio gestione su menú/productos
#     pass

# @business_bp.route('/orders')
# @business_required
# def incoming_orders():
#     # Lógica para mostrar los pedidos entrantes al negocio
#     pass












# # --- MOCK DATA para el comercio ---
# MOCK_BUSINESS_INFO = {
    # 'id': 101,
    # 'name': 'Pizzería La Clásica',
    # 'address': 'Calle 20 #15-30, Centro, Yopal',
    # 'phone': '3101234567',
    # 'email': 'laclasica@example.com',
    # 'description': 'Las mejores pizzas artesanales de Yopal, con ingredientes frescos y un toque de tradición.',
    # 'logo': 'pizzeria-la-clasica-logo.png',
    # 'status': 'Abierto', # O 'Cerrado'
    # 'min_order_value': 15000,
    # 'delivery_fee': 4000,
    # 'delivery_time_avg': '30-45 min',
    # 'payment_methods': ['Efectivo', 'Tarjeta (online)', 'Datafono'],
    # 'categories': ['Comida', 'Pizzas', 'Italiana'],
    # 'rating': 4.7,
    # 'reviews_count': 125,
    # 'opening_hours': [
        # {'day': 'Lunes', 'hours': '12:00 - 22:00'},
        # {'day': 'Martes', 'hours': '12:00 - 22:00'},
        # {'day': 'Miércoles', 'hours': '12:00 - 22:00'},
        # {'day': 'Jueves', 'hours': '12:00 - 22:00'},
        # {'day': 'Viernes', 'hours': '12:00 - 23:00'},
        # {'day': 'Sábado', 'hours': '12:00 - 23:00'},
        # {'day': 'Domingo', 'hours': '12:00 - 21:00'},
    # ]
# }

# MOCK_ACTIVE_ORDERS = [
    # {
        # 'id': 3001,
        # 'customer_name': 'Sofía García',
        # 'delivery_address': 'Carrera 25 #40-10, Apto 502',
        # 'total_amount': 45000,
        # 'payment_method': 'Tarjeta (online)',
        # 'order_time': '2025-06-01 14:05',
        # 'status': 'Nuevo Pedido', # 'Nuevo Pedido', 'En Preparación', 'Listo para Recoger', 'En Camino', 'Entregado', 'Cancelado'
        # 'items': [
            # {'name': 'Pizza Pepperoni Mediana', 'quantity': 1, 'price': 28000},
            # {'name': 'Gaseosa Coca-Cola 1.5L', 'quantity': 1, 'price': 6000},
            # {'name': 'Palitos de Ajo', 'quantity': 1, 'price': 11000},
        # ],
        # 'customer_notes': 'Sin cebolla por favor.'
    # },
    # {
        # 'id': 3002,
        # 'customer_name': 'Carlos Montes',
        # 'delivery_address': 'Calle 10 #3-15, Casa 2',
        # 'total_amount': 32000,
        # 'payment_method': 'Efectivo',
        # 'order_time': '2025-06-01 13:50',
        # 'status': 'En Preparación',
        # 'items': [
            # {'name': 'Pizza Hawaiana Grande', 'quantity': 1, 'price': 32000},
        # ],
        # 'customer_notes': 'Llamar antes de llegar.'
    # }
# ]

# MOCK_MENU_ITEMS = [
    # {
        # 'id': 1,
        # 'name': 'Pizza Pepperoni',
        # 'description': 'Clásica pizza con salsa de tomate, mozzarella y abundante pepperoni.',
        # 'price': 28000,
        # 'category': 'Pizzas Clásicas',
        # 'image': 'pizza_pepperoni.jpg',
        # 'available': True
    # },
    # {
        # 'id': 2,
        # 'name': 'Pizza Hawaiana',
        # 'description': 'Jamón, piña y queso mozzarella. Una explosión de sabor tropical.',
        # 'price': 30000,
        # 'category': 'Pizzas Clásicas',
        # 'image': 'pizza_hawaiana.jpg',
        # 'available': True
    # },
    # {
        # 'id': 3,
        # 'name': 'Lasaña Bolognesa',
        # 'description': 'Capas de pasta, carne bolognesa, salsa bechamel y queso.',
        # 'price': 25000,
        # 'category': 'Pastas',
        # 'image': 'lasagna_bolognesa.jpg',
        # 'available': True
    # },
    # {
        # 'id': 4,
        # 'name': 'Agua Mineral (600ml)',
        # 'description': 'Agua embotellada natural.',
        # 'price': 3000,
        # 'category': 'Bebidas',
        # 'image': 'agua_mineral.jpg',
        # 'available': True
    # },
    # {
        # 'id': 5,
        # 'name': 'Tiramisú',
        # 'description': 'Postre italiano clásico con café, bizcochos y mascarpone.',
        # 'price': 12000,
        # 'category': 'Postres',
        # 'image': 'tiramisu.jpg',
        # 'available': False # Ejemplo de un item no disponible
    # }
# ]

# MOCK_SALES_HISTORY = [
    # {
        # 'id': 2001,
        # 'date': '2025-05-30',
        # 'total_sales': 150000,
        # 'orders_count': 5
    # },
    # {
        # 'id': 2002,
        # 'date': '2025-05-29',
        # 'total_sales': 210000,
        # 'orders_count': 7
    # },
    # {
        # 'id': 2003,
        # 'date': '2025-05-28',
        # 'total_sales': 185000,
        # 'orders_count': 6
    # },
# ]

# # Helper para obtener el cliente y negocio del mock data (simulación)
# def get_mock_customer_and_business(order_id):
    # order = next((o for o in MOCK_ACTIVE_ORDERS if o['id'] == order_id), None)
    # if not order: return None, None, None

    # # Simular datos del cliente y negocio para el correo
    # # En un sistema real, los buscarías en la DB
    # mock_customer = {
        # 'name': order['customer_name'],
        # 'email': 'cliente_ejemplo@mailinator.com', # Correo real del cliente aquí
        # 'id': 1 # Simulado
    # }
    # mock_business = {
        # 'name': MOCK_BUSINESS_INFO['name'],
        # 'email': MOCK_BUSINESS_INFO['email'],
        # 'id': MOCK_BUSINESS_INFO['id']
    # }
    # return order, mock_customer, mock_business


# # Actualizar estado del pedido (simulado)
# @business_bp.route('/orders/<int:order_id>/update_status', methods=['POST'])
# # @login_required
# def update_order_status(order_id):
    # new_status = request.form['new_status']
    
    # order, customer, business = get_mock_customer_and_business(order_id)

    # if not order:
        # flash('Pedido no encontrado.', 'danger')
        # return redirect(url_for('business.orders'))

    # # Actualizar estado del pedido en MOCK_ACTIVE_ORDERS (simulación de DB)
    # for o in MOCK_ACTIVE_ORDERS:
        # if o['id'] == order_id:
            # o['status'] = new_status
            # break

    # flash(f'Estado del pedido #{order_id} actualizado a: {new_status}', 'success')

    # # --- Lógica de Notificación por Correo ---
    # # 1. Notificación al Cliente
    # if customer:
        # customer_email = customer['email']
        # customer_name = customer['name']
        # track_order_url = url_for('customer.track_order', order_id=order.id, _external=True) # URL completa
        # current_app.jinja_env.globals['send_email_notification'](
            # recipient_email=customer_email,
            # subject=f"Tu Pedido #{order.id} ha sido actualizado: {new_status}",
            # template='emails/order_status_update_customer.html',
            # order=order,
            # customer_name=customer_name,
            # new_status=new_status,
            # track_order_url=track_order_url,
            # current_year=2025 # Pasa el año actual a la plantilla
        # )
    
    # # 2. Notificación al Comercio (si es un nuevo pedido, para que el comercio lo reciba)
    # # Esta notificación es solo para el estado 'Nuevo Pedido'
    # if new_status == 'Nuevo Pedido' and business: # O disparar desde el punto de creación del pedido
        # business_email = business['email']
        # business_name = business['name']
        # dashboard_url = url_for('business.orders', _external=True) # URL completa al dashboard de pedidos del comercio
        # current_app.jinja_env.globals['send_email_notification'](
            # recipient_email=business_email,
            # subject=f"¡Nuevo Pedido Recibido! Pedido #{order.id}",
            # template='emails/new_order_business.html',
            # order=order,
            # business_name=business_name,
            # dashboard_url=dashboard_url,
            # current_year=2025
        # )

    # # Nota: La notificación al motorizado se gestiona cuando se le ASIGNA un pedido,
    # # no cuando el comercio lo actualiza (a menos que el comercio directamente asigne).
    # # Esa lógica irá en driver_routes.py o en un módulo de asignación.

    # # Lógica para actualizar el estado del pedido en la DB
    # # Por simplicidad, solo flash y redirigimos
    # flash(f'Estado del pedido #{order_id} actualizado a: {new_status}', 'success')
    # return redirect(url_for('business.order_details', order_id=order_id))



# # # Dashboard del comercio
# # @business_bp.route('/dashboard')
# # # @login_required # Protege esta ruta, solo para usuarios logueados como comercio
# # def dashboard():
    # # # En una aplicación real, se consultarían los datos de pedidos, ventas, etc.
    # # return render_template('business/dashboard.html', 
                           # # business_info=MOCK_BUSINESS_INFO,
                           # # active_orders=MOCK_ACTIVE_ORDERS)

# # Gestión de pedidos (lista)
# @business_bp.route('/orders')
# # @login_required
# def orders():
    # status_filter = request.args.get('status', 'all')
    
    # if status_filter == 'all':
        # filtered_orders = MOCK_ACTIVE_ORDERS # En un caso real, incluir historial
    # else:
        # filtered_orders = [o for o in MOCK_ACTIVE_ORDERS if o['status'] == status_filter]

    # return render_template('business/orders.html', 
                           # active_orders=filtered_orders, 
                           # status_filter=status_filter)

# # Detalles de un pedido específico
# @business_bp.route('/orders/<int:order_id>')
# # @login_required
# def order_details(order_id):
    # order = next((o for o in MOCK_ACTIVE_ORDERS if o['id'] == order_id), None)
    # if not order:
        # flash('Pedido no encontrado.', 'danger')
        # return redirect(url_for('business.orders'))
    
    # return render_template('business/order_details.html', order=order)

# # Actualizar estado del pedido (simulado)
# # @business_bp.route('/orders/<int:order_id>/update_status', methods=['POST'])
# # # @login_required
# # def update_order_status(order_id):
    # # new_status = request.form['new_status']
    
    # # # Lógica para actualizar el estado del pedido en la DB
    # # # Por simplicidad, solo flash y redirigimos
    # # flash(f'Estado del pedido #{order_id} actualizado a: {new_status}', 'success')
    # # return redirect(url_for('business.order_details', order_id=order_id))

# Gestión de menú/productos
@business_bp.route('/menu', methods=['GET', 'POST'])
@business_required
def menu_management():
    business = Business.query.filter_by(user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        name = request.form.get('item_name')
        price = request.form.get('item_price')
        description = request.form.get('item_description')
        category_name = request.form.get('item_category')
        is_available = True if request.form.get('item_available') else False

        # Manejo categoría
        category = None
        if category_name:
            category = Category.query.filter_by(name=category_name, business_id=business.id).first()
            if not category:
                category = Category(name=category_name, business_id=business.id)
                db.session.add(category)

        new_product = Product(
            name=name,
            description=description,
            price=float(price),
            business_id=business.id,
            is_available=is_available,
            category=category
        )

        db.session.add(new_product)
        db.session.commit()

        flash('Producto creado correctamente', 'success')
        return redirect(url_for('business.menu_management'))

    menu_items = Product.query.filter_by(business_id=business.id).all()

    return render_template(
        'business/menu_management.html',
        business=business,
        menu_items=menu_items
    )

# Toggle disponibilidad de un producto (simulado)
@business_bp.route('/menu/<int:item_id>/toggle', methods=['POST'])
@business_required
def toggle_item_availability(item_id):
    business = Business.query.filter_by(user_id=current_user.id).first_or_404()

    product = Product.query.filter_by(id=item_id, business_id=business.id).first_or_404()

    product.is_available = not product.is_available
    db.session.commit()

    return redirect(url_for('business.menu_management'))

# # Gestión de información del negocio
@business_bp.route('/info', methods=['GET', 'POST'])
@business_required
def business_info():
    business = Business.query.filter_by(user_id=current_user.id).first_or_404()

    if request.method == 'POST':

        # Solo actualizar si el campo existe en el form enviado
        if 'business_name' in request.form:
            business.name = request.form.get('business_name')
            business.phone = request.form.get('business_phone')
            business.address = request.form.get('business_address')
            business.description = request.form.get('business_description')

        if 'min_order_value' in request.form:
            business.min_order_value = request.form.get('min_order_value') or 0
            business.delivery_fee = request.form.get('delivery_fee') or 0

        if 'payment_method' in request.form:
            business.payment_methods = request.form.getlist('payment_method')

        db.session.commit()
        flash('Información actualizada correctamente', 'success')
        return redirect(url_for('business.business_info'))

    return render_template(
        'business/business_info.html',
        business=business
    )    

# # Historial de ventas
# @business_bp.route('/sales-history')
# # @login_required
# def sales_history():
    # return render_template('business/sales_history.html', sales_data=MOCK_SALES_HISTORY)