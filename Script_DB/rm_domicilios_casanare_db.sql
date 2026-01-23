-- Database: rm_domicilios_casanare_db

-- DROP DATABASE IF EXISTS rm_domicilios_casanare_db;

CREATE DATABASE rm_domicilios_casanare_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Colombia.1252'
    LC_CTYPE = 'Spanish_Colombia.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

COMMENT ON DATABASE rm_domicilios_casanare_db
    IS 'Nuevo modelo relacional plataforma web domicilios multiservicios RM 01062025';



-- rm_domicilios_yopal_db_schema.sql
--
-- Script SQL para la creación de tablas, relaciones e índices
-- de la plataforma web de domicilios multiservicios RM.
-- Este esquema está sincronizado con el archivo models.py actual.
--
-- NOTA: Si ya tienes una base de datos con el mismo nombre y datos,
-- este script la ELIMINARÁ y la volverá a crear. Úsalo con precaución en producción.

-- Eliminar el esquema public si existe y recrearlo para asegurar una limpieza total
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- Crear la extensión UUID si es necesaria para futuros usos (opcional)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'customer', -- 'customer', 'driver', 'business', 'admin'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_role ON users (role);

-- Tabla customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    phone_number VARCHAR(20) UNIQUE,
    address VARCHAR(255),
    profile_picture VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_customers_user_id ON customers (user_id);
CREATE INDEX ix_customers_phone_number ON customers (phone_number);

-- Tabla drivers
CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50) NOT NULL,
    license_plate VARCHAR(20) UNIQUE,
    is_available BOOLEAN DEFAULT TRUE,
    current_location VARCHAR(255),
    rating REAL DEFAULT 0.0,
    total_deliveries INTEGER DEFAULT 0,
    profile_picture VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_drivers_user_id ON drivers (user_id);
CREATE INDEX ix_drivers_phone_number ON drivers (phone_number);
CREATE INDEX ix_drivers_license_plate ON drivers (license_plate);
CREATE INDEX ix_drivers_is_available ON drivers (is_available);


-- Tabla businesses
CREATE TABLE businesses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    address VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    description TEXT,
    logo VARCHAR(255),
    status VARCHAR(20) DEFAULT 'Cerrado', -- 'Abierto', 'Cerrado', 'De Vacaciones'
    min_order_value INTEGER DEFAULT 0,
    delivery_fee INTEGER DEFAULT 0,
    average_delivery_time VARCHAR(50),
    rating REAL DEFAULT 0.0,
    reviews_count INTEGER DEFAULT 0,
    slug VARCHAR(120) NOT NULL UNIQUE, -- Para URLs amigables
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_businesses_user_id ON businesses (user_id);
CREATE INDEX ix_businesses_slug ON businesses (slug);
CREATE INDEX ix_businesses_status ON businesses (status);
CREATE INDEX ix_businesses_name ON businesses (name);


-- Tabla opening_hours
CREATE TABLE opening_hours (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    day_of_week VARCHAR(15) NOT NULL,
    hours VARCHAR(50) NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses (id) ON DELETE CASCADE
);
CREATE INDEX ix_opening_hours_business_id ON opening_hours (business_id);
CREATE INDEX ix_opening_hours_day_of_week ON opening_hours (day_of_week);


-- Tabla payment_methods (maestro)
CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);
CREATE INDEX ix_payment_methods_name ON payment_methods (name);


-- Tabla business_payment_methods (tabla de unión N:M)
CREATE TABLE business_payment_methods (
    business_id INTEGER NOT NULL,
    payment_method_id INTEGER NOT NULL,
    PRIMARY KEY (business_id, payment_method_id),
    FOREIGN KEY (business_id) REFERENCES businesses (id) ON DELETE CASCADE,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods (id) ON DELETE CASCADE
);
CREATE INDEX ix_business_payment_methods_business_id ON business_payment_methods (business_id);
CREATE INDEX ix_business_payment_methods_payment_method_id ON business_payment_methods (payment_method_id);


-- Tabla categories (maestro)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);
CREATE INDEX ix_categories_name ON categories (name);


-- Tabla business_categories (tabla de unión N:M)
CREATE TABLE business_categories (
    business_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (business_id, category_id),
    FOREIGN KEY (business_id) REFERENCES businesses (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
);
CREATE INDEX ix_business_categories_business_id ON business_categories (business_id);
CREATE INDEX ix_business_categories_category_id ON business_categories (category_id);


-- Tabla products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    category VARCHAR(80), -- Campo de texto para la categoría del producto dentro del negocio
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses (id) ON DELETE CASCADE
);
CREATE INDEX ix_products_business_id ON products (business_id);
CREATE INDEX ix_products_name ON products (name);
CREATE INDEX ix_products_is_available ON products (is_available);


-- Tabla orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    business_id INTEGER NOT NULL,
    driver_id INTEGER, -- Puede ser NULL hasta que se asigne un motorizado
    order_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivery_address VARCHAR(255) NOT NULL,
    total_amount INTEGER NOT NULL,
    delivery_fee INTEGER NOT NULL DEFAULT 0,
    service_fee INTEGER NOT NULL DEFAULT 0,
    payment_method VARCHAR(50) NOT NULL, -- Nombre del método de pago utilizado (ej. 'Efectivo')
    status VARCHAR(50) NOT NULL DEFAULT 'Pendiente', -- Ej. 'Pendiente', 'Preparando', 'En camino', 'Entregado', 'Cancelado'
    customer_notes TEXT,
    driver_notes TEXT,
    pickup_time TIMESTAMP WITHOUT TIME ZONE,
    delivery_time TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (customer_id) REFERENCES customers (id),
    FOREIGN KEY (business_id) REFERENCES businesses (id),
    FOREIGN KEY (driver_id) REFERENCES drivers (id)
);
CREATE INDEX ix_orders_customer_id ON orders (customer_id);
CREATE INDEX ix_orders_business_id ON orders (business_id);
CREATE INDEX ix_orders_driver_id ON orders (driver_id);
CREATE INDEX ix_orders_status ON orders (status);
CREATE INDEX ix_orders_order_time ON orders (order_time);


-- Tabla order_items
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_order INTEGER NOT NULL, -- Precio del producto en el momento del pedido
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id)
);
CREATE INDEX ix_order_items_order_id ON order_items (order_id);
CREATE INDEX ix_order_items_product_id ON order_items (product_id);	