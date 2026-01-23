# rm_domicilios_yopal/populate_db.py

# Importa 'app' desde app.py y 'db' y los modelos desde models.py
from app import app
from models import db, PaymentMethod, Category

from sqlalchemy.exc import IntegrityError

# ***************************************************************
# ¡CAMBIO CLAVE AQUÍ!
# Es crucial envolver las operaciones de base de datos dentro de un contexto de aplicación Flask
with app.app_context():
# ***************************************************************
    print("Iniciando la adición de datos iniciales...")

    # Añadir métodos de pago
    payment_methods_to_add = ['Efectivo', 'Tarjeta (online)', 'Datafono', 'Nequi', 'Daviplata']
    for pm_name in payment_methods_to_add:
        # Aquí PaymentMethod.query.filter_by... ya estará en el contexto de la app
        if not PaymentMethod.query.filter_by(name=pm_name).first():
            db.session.add(PaymentMethod(name=pm_name))
            print(f"  - Añadido método de pago: {pm_name}")
        else:
            print(f"  - Método de pago '{pm_name}' ya existe, omitiendo.")
    
    # Añadir categorías de negocio
    categories_to_add = ['Pizzas', 'Comida Rápida', 'Asiática', 'Vegetariana', 'Postres', 'Bebidas', 'Mercado', 'Farmacia', 'Otros', 'Tecnología', 'Belleza']
    for cat_name in categories_to_add:
        # Aquí Category.query.filter_by... ya estará en el contexto de la app
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
            print(f"  - Añadida categoría: {cat_name}")
        else:
            print(f"  - Categoría '{cat_name}' ya existe, omitiendo.")

    try:
        db.session.commit()
        print("Datos iniciales de PaymentMethod y Category añadidos/verificados exitosamente.")
    except IntegrityError:
        db.session.rollback()
        print("Error de integridad: Algunos datos ya existían o hubo un problema al intentar añadirlos. Revertiendo.")
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al añadir datos iniciales: {e}. Revertiendo.")

    print("Proceso de adición de datos iniciales finalizado.")