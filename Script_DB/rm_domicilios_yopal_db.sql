-- ##################################################################################################################
-- # SCRIPT COMPLETO DE BASE DE DATOS PARA PLATAFORMA DE DOMICILIOS MULTI-SERVICIO (PostgreSQL)                     #
-- # Este script crea todas las tablas, relaciones, índices y datos de ejemplo para una plataforma robusta y escalable. #
-- ##################################################################################################################

-- Paso 1: Eliminar tablas existentes (para un inicio limpio, si se ejecuta varias veces)
-- Se eliminan en orden inverso de dependencia para evitar errores de clave foránea.
DROP TABLE IF EXISTS historial_estados_pedido CASCADE;
DROP TABLE IF EXISTS pagos CASCADE;
DROP TABLE IF EXISTS detalles_pedido CASCADE;
DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS detalles_item_compra CASCADE;
DROP TABLE IF EXISTS detalles_paquete_envio CASCADE;
DROP TABLE IF EXISTS formas_pago CASCADE;
DROP TABLE IF EXISTS direcciones_genericas CASCADE;
DROP TABLE IF EXISTS direcciones_cliente CASCADE;
DROP TABLE IF EXISTS motorizados CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS categorias_comida_producto CASCADE;
DROP TABLE IF EXISTS restaurantes CASCADE;
DROP TABLE IF EXISTS servicios CASCADE; -- Antes categorias_producto
DROP TABLE IF EXISTS usuarios CASCADE;

-- ##################################################################################################################
-- # DEFINICIÓN DE TABLAS                                                                                           #
-- ##################################################################################################################

-- Tabla de Usuarios (Clientes y Administradores)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rol VARCHAR(20) NOT NULL DEFAULT 'cliente' -- 'cliente', 'administrador'
);
CREATE INDEX idx_usuarios_email ON usuarios (email);

-- Tabla de Servicios (Generaliza las categorías de alto nivel como 'Comida', 'Paquetes', 'Compras')
CREATE TABLE servicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT
);
CREATE INDEX idx_servicios_nombre ON servicios (nombre);

-- Tabla de Restaurantes (Específica para el servicio de 'Comida')
CREATE TABLE restaurantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT NOT NULL,
    telefono VARCHAR(20),
    horario_atencion VARCHAR(255),
    descripcion TEXT,
    logo_url VARCHAR(255),
    latitud DECIMAL(9, 6), -- Coordenadas para geolocalización
    longitud DECIMAL(9, 6)  -- Coordenadas para geolocalización
);
CREATE INDEX idx_restaurantes_nombre ON restaurantes (nombre);

-- Tabla de Categorías de Productos de Comida (Específica para productos dentro del servicio de 'Comida')
CREATE TABLE categorias_comida_producto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
);
CREATE INDEX idx_categorias_comida_producto_nombre ON categorias_comida_producto (nombre);

-- Tabla de Productos (Específica para ítems del servicio de 'Comida')
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    imagen_url VARCHAR(255),
    restaurante_id INTEGER NOT NULL REFERENCES restaurantes(id) ON DELETE CASCADE,
    categoria_id INTEGER NOT NULL REFERENCES categorias_comida_producto(id) ON DELETE RESTRICT
);
CREATE INDEX idx_productos_restaurante_id ON productos (restaurante_id);
CREATE INDEX idx_productos_categoria_id ON productos (categoria_id);

-- Tabla de Motorizados
CREATE TABLE motorizados (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    documento_identidad VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(255) UNIQUE,
    placa_vehiculo VARCHAR(10),
    disponible BOOLEAN DEFAULT TRUE,
    ubicacion_actual POINT, -- Requiere extensión PostGIS si se necesita funcionalidad geográfica avanzada
    contrasena VARCHAR(255) NOT NULL, -- Contraseña para el login del motorizado
    rol VARCHAR(20) DEFAULT 'motorizado',
    saldo_cuenta DECIMAL(10, 2) DEFAULT 0.00
);
CREATE INDEX idx_motorizados_documento_identidad ON motorizados (documento_identidad);
CREATE INDEX idx_motorizados_disponible ON motorizados (disponible);
-- CREATE INDEX idx_motorizados_ubicacion ON motorizados USING GIST (ubicacion_actual); -- Para consultas espaciales eficientes (descomentar si PostGIS está habilitado)

-- Tabla de Direcciones de Cliente
CREATE TABLE direcciones_cliente (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    direccion TEXT NOT NULL,
    alias VARCHAR(100),
    es_principal BOOLEAN DEFAULT FALSE,
    latitud DECIMAL(9, 6),
    longitud DECIMAL(9, 6),
    UNIQUE (cliente_id, direccion) -- Evita direcciones duplicadas para el mismo cliente
);
CREATE INDEX idx_direcciones_cliente_cliente_id ON direcciones_cliente (cliente_id);

-- Tabla de Direcciones Genéricas (Para orígenes/destinos de paquetes que no son direcciones de clientes registrados)
CREATE TABLE direcciones_genericas (
    id SERIAL PRIMARY KEY,
    direccion TEXT NOT NULL,
    latitud DECIMAL(9, 6),
    longitud DECIMAL(9, 6),
    notas TEXT -- Notas adicionales sobre la dirección
);
CREATE INDEX idx_direcciones_genericas_direccion ON direcciones_genericas (direccion);

-- Tabla de Formas de Pago
CREATE TABLE formas_pago (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT
);
CREATE INDEX idx_formas_pago_nombre ON formas_pago (nombre);

-- Tabla de Detalles de Paquetes de Envío (Reemplaza la antigua tabla 'paquetes', almacena detalles de CADA envío)
CREATE TABLE detalles_paquete_envio (
    id SERIAL PRIMARY KEY,
    tipo_paquete VARCHAR(255) NOT NULL, -- Ej. 'documento', 'caja_pequeña', 'caja_mediana', 'caja_grande'
    direccion_recogida TEXT NOT NULL, -- Dirección de recogida como texto
    tamano_paquete VARCHAR(20), -- Ej. 'pequeño', 'mediano', 'grande'
    direccion_entrega TEXT NOT NULL, -- Dirección de entrega como texto
    descripcion TEXT, -- Descripción del contenido del paquete
    origen_direccion_id INTEGER REFERENCES direcciones_cliente(id) ON DELETE RESTRICT, -- Opcional, si el origen es una dirección de cliente
    destino_direccion_id INTEGER REFERENCES direcciones_cliente(id) ON DELETE RESTRICT, -- Opcional, si el destino es una dirección de cliente
    peso_kg DECIMAL(10, 2),
    dimensiones_cm VARCHAR(50), -- Ej. "10x20x5"
    valor_declarado DECIMAL(10, 2), -- Valor declarado del paquete para seguro
    instrucciones_especiales TEXT,
    precio_calculado DECIMAL(10, 2) NOT NULL -- El costo final del envío del paquete
);
CREATE INDEX idx_detalles_paquete_envio_tipo_paquete ON detalles_paquete_envio (tipo_paquete);

-- Tabla de Detalles de Ítems de Compra (Para el servicio de 'Compras')
CREATE TABLE detalles_item_compra (
    id SERIAL PRIMARY KEY,
    descripcion_item TEXT NOT NULL, -- Descripción del ítem a comprar (ej. "Leche entera Alpina 1L", "Pan tajado Bimbo")
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_estimado DECIMAL(10, 2), -- Precio que el cliente estima, puede ser actualizado por motorizado
    notas_especificas TEXT, -- Ej. "si no hay Alpina, traer Colanta"
    tienda_preferida VARCHAR(255) -- Ej. "Supermercado Éxito", "Tienda de barrio"
);
CREATE INDEX idx_detalles_item_compra_descripcion ON detalles_item_compra (descripcion_item);

-- Tabla de Pedidos (Unificada para todos los servicios)
CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    servicio_id INTEGER NOT NULL REFERENCES servicios(id) ON DELETE RESTRICT, -- Tipo de servicio (comida, paquetes, compras)
    direccion_entrega_id INTEGER NOT NULL REFERENCES direcciones_cliente(id) ON DELETE RESTRICT,
    fecha_pedido TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) NOT NULL DEFAULT 'pendiente', -- Ej. 'pendiente', 'aceptado', 'en_camino', 'entregado', 'cancelado'
    total DECIMAL(10, 2) NOT NULL, -- Suma de los subtotales de detalles_pedido + costo_domicilio
    costo_domicilio DECIMAL(10, 2) DEFAULT 0.00,
    notas TEXT,
    motorizado_id INTEGER REFERENCES motorizados(id) ON DELETE SET NULL,
    fecha_asignacion TIMESTAMP WITH TIME ZONE,
    fecha_entrega TIMESTAMP WITH TIME ZONE,
    forma_pago_id INTEGER REFERENCES formas_pago(id) ON DELETE RESTRICT -- Forma de pago para este pedido
);
CREATE INDEX idx_pedidos_cliente_id ON pedidos (cliente_id);
CREATE INDEX idx_pedidos_servicio_id ON pedidos (servicio_id);
CREATE INDEX idx_pedidos_motorizado_id ON pedidos (motorizado_id);
CREATE INDEX idx_pedidos_estado ON pedidos (estado);

-- Tabla de Detalles del Pedido (Unificada, referencia a los ítems específicos de cada servicio)
CREATE TABLE detalles_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    tipo_item VARCHAR(50) NOT NULL, -- 'producto_comida', 'paquete_envio', 'item_lista_compra'
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10, 2) NOT NULL, -- Precio unitario del ítem en este detalle
    
    -- Claves foráneas condicionales (solo una de ellas estará llena por detalle)
    producto_id INTEGER REFERENCES productos(id) ON DELETE RESTRICT,             -- Para ítems de comida
    paquete_envio_id INTEGER REFERENCES detalles_paquete_envio(id) ON DELETE RESTRICT, -- Para ítems de paquete
    item_compra_id INTEGER REFERENCES detalles_item_compra(id) ON DELETE RESTRICT,   -- Para ítems de compra

    -- Restricción para asegurar que solo una de las FKs de ítem esté llena
    CONSTRAINT chk_one_item_type CHECK (
        (producto_id IS NOT NULL AND paquete_envio_id IS NULL AND item_compra_id IS NULL AND tipo_item = 'producto_comida') OR
        (producto_id IS NULL AND paquete_envio_id IS NOT NULL AND item_compra_id IS NULL AND tipo_item = 'paquete_envio') OR
        (producto_id IS NULL AND paquete_envio_id IS NULL AND item_compra_id IS NOT NULL AND tipo_item = 'item_lista_compra')
    )
);
CREATE INDEX idx_detalles_pedido_pedido_id ON detalles_pedido (pedido_id);
CREATE INDEX idx_detalles_pedido_tipo_item ON detalles_pedido (tipo_item);
CREATE INDEX idx_detalles_pedido_producto_id ON detalles_pedido (producto_id);
CREATE INDEX idx_detalles_pedido_paquete_envio_id ON detalles_pedido (paquete_envio_id);
CREATE INDEX idx_detalles_pedido_item_compra_id ON detalles_pedido (item_compra_id);


-- Tabla de Pagos
CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL UNIQUE REFERENCES pedidos(id) ON DELETE CASCADE,
    forma_pago_id INTEGER NOT NULL REFERENCES formas_pago(id) ON DELETE RESTRICT,
    fecha_pago TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10, 2) NOT NULL,
    transaccion_id VARCHAR(255), -- ID de transacción de pasarela de pago
    estado_pago VARCHAR(50) NOT NULL DEFAULT 'pendiente' -- 'pendiente', 'completado', 'fallido', 'reembolsado'
);
CREATE INDEX idx_pagos_pedido_id ON pagos (pedido_id);
CREATE INDEX idx_pagos_forma_pago_id ON pagos (forma_pago_id);

-- Tabla de Historial de Estados del Pedido
CREATE TABLE historial_estados_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    estado VARCHAR(50) NOT NULL,
    fecha_cambio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    usuario_cambio_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL -- Quién realizó el cambio (puede ser un administrador o motorizado)
);
CREATE INDEX idx_historial_estados_pedido_pedido_id ON historial_estados_pedido (pedido_id);
CREATE INDEX idx_historial_estados_pedido_estado ON historial_estados_pedido (estado);


-- ##################################################################################################################
-- # INSERCIÓN DE DATOS DE EJEMPLO                                                                                  #
-- ##################################################################################################################

-- Insertar datos de usuario
INSERT INTO usuarios (nombre, apellido, email, contrasena, telefono, fecha_registro, rol)
VALUES ('Neiro00', 'Culma Cliente00', 'Neiroc.700@gmail.com','12345','3123495917','2025-05-18 17:48:09.122013-05','cliente')
ON CONFLICT (email) DO NOTHING;

-- Insertar datos de motorizados
INSERT INTO motorizados (nombre, apellido, documento_identidad, telefono, email, placa_vehiculo, disponible, ubicacion_actual, contrasena, rol, saldo_cuenta)
VALUES ('prueba', 'prueba', '10000000000', '312000000', 'prueba@gmail.com', 'PRU00E',TRUE,'(4.6091,-74.0721)', 'Prueba123', 'motorizado',6900.00)
ON CONFLICT (documento_identidad) DO NOTHING;

-- Insertar datos de restaurantes
INSERT INTO restaurantes (nombre, direccion, telefono, horario_atencion, descripcion, logo_url, latitud, longitud)
VALUES ('Casa china', 'Cra 23 19-22', '3115781124', 'Lunes a viernes 7 am - 15 horas', 'Encuentras la mejor comida china de Yopal.', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSbenTuy9H1iBCLDlARKK6fs9wCM6Fwq0FNwQ&s', 5.341251, -72.393310)
ON CONFLICT (nombre) DO NOTHING;

-- Insertar formas de pago
INSERT INTO formas_pago (nombre, descripcion) VALUES ('efectivo', 'Pago en efectivo al motorizado') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO formas_pago (nombre, descripcion) VALUES ('nequi', 'Pago a través de Nequi') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO formas_pago (nombre, descripcion) VALUES ('daviplata', 'Pago a través de Daviplata') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO formas_pago (nombre, descripcion) VALUES ('tarjeta de Crédito', 'Pago con tarjeta de crédito') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO formas_pago (nombre, descripcion) VALUES ('tarjeta Débito', 'Pago con tarjeta de débito') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO formas_pago (nombre, descripcion) VALUES ('transferencia Bancaria', 'Pago por transferencia bancaria') ON CONFLICT (nombre) DO NOTHING;

-- Insertar servicios (generalizados)
INSERT INTO servicios (nombre, descripcion) VALUES ('comidas', 'Servicio de entrega de alimentos de restaurantes') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO servicios (nombre, descripcion) VALUES ('paquetes', 'Servicio de envío y recogida de paquetes') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO servicios (nombre, descripcion) VALUES ('pagos servicios', 'Servicio para realizar pagos de facturas o servicios') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO servicios (nombre, descripcion) VALUES ('diligencias', 'Servicio para realizar diligencias y trámites') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO servicios (nombre, descripcion) VALUES ('compras', 'Servicio para realizar compras en tiendas y supermercados') ON CONFLICT (nombre) DO NOTHING;

-- Insertar categorías de comida de ejemplo
INSERT INTO categorias_comida_producto (nombre) VALUES ('Sushi') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO categorias_comida_producto (nombre) VALUES ('Platos Fuertes') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO categorias_comida_producto (nombre) VALUES ('Bebidas') ON CONFLICT (nombre) DO NOTHING;

-- Insertar una dirección para el cliente de ejemplo (CRUCIAL para evitar errores de FK)
INSERT INTO direcciones_cliente (cliente_id, direccion, alias, es_principal, latitud, longitud)
VALUES (
    (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1),
    'Calle Falsa 123, Ciudad Ejemplo, Barrio Central',
    'Casa Principal',
    TRUE,
    4.6091,
    -74.0721
) ON CONFLICT (cliente_id, direccion) DO NOTHING;

-- Insertar productos de comida de ejemplo
INSERT INTO productos (nombre, descripcion, precio, imagen_url, restaurante_id, categoria_id)
VALUES (
    'Sushi00',
    'Plato pequeño de sushi variado',
    21000.00,
    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSBSKGJulSuNoHuymU9oqia_QE-sylW5IF53TiAbY9qhzd4_9n1ZB6Xan0TFZQwbsRisvxfYg&s',
    (SELECT id FROM restaurantes WHERE nombre = 'Casa china' LIMIT 1),
    (SELECT id FROM categorias_comida_producto WHERE nombre = 'Sushi' LIMIT 1)
) ON CONFLICT (nombre, restaurante_id) DO NOTHING;

INSERT INTO productos (nombre, descripcion, precio, imagen_url, restaurante_id, categoria_id)
VALUES (
    'Arroz frito con pollo',
    'Delicioso arroz frito con trozos de pollo y vegetales',
    18000.00,
    'https://ejemplo.com/arroz_frito.jpg',
    (SELECT id FROM restaurantes WHERE nombre = 'Casa china' LIMIT 1),
    (SELECT id FROM categorias_comida_producto WHERE nombre = 'Platos Fuertes' LIMIT 1)
) ON CONFLICT (nombre, restaurante_id) DO NOTHING;

-- Insertar detalles de paquete de envío de ejemplo
INSERT INTO detalles_paquete_envio (
    tipo_paquete,
    direccion_recogida,
    tamano_paquete,
    direccion_entrega,
    descripcion,
    origen_direccion_id,
    destino_direccion_id,
    peso_kg,
    dimensiones_cm,
    valor_declarado,
    instrucciones_especiales,
    precio_calculado
)
VALUES (
    'caja',
    'Cra 10 18-10, Centro',
    'mediano',
    'Calle 40 10-15, Norte',
    'Documentos importantes, frágil',
    (SELECT id FROM direcciones_cliente WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) LIMIT 1),
    (SELECT id FROM direcciones_cliente WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) LIMIT 1),
    2.5,
    '30x20x15',
    50000.00,
    'Llamar al destinatario al llegar',
    12000.00
) ON CONFLICT (tipo_paquete, direccion_recogida, direccion_entrega) DO NOTHING;

-- Insertar detalles de ítem de compra de ejemplo
INSERT INTO detalles_item_compra (
    descripcion_item,
    cantidad,
    precio_estimado,
    notas_especificas,
    tienda_preferida
)
VALUES (
    'Leche entera Alpina 1L',
    2,
    3500.00,
    'Si no hay Alpina, traer Colanta',
    'Supermercado Éxito'
) ON CONFLICT (descripcion_item, cantidad, tienda_preferida) DO NOTHING;

INSERT INTO detalles_item_compra (
    descripcion_item,
    cantidad,
    precio_estimado,
    notas_especificas,
    tienda_preferida
)
VALUES (
    'Pan tajado Bimbo integral',
    1,
    5000.00,
    'Fecha de vencimiento larga',
    'Panadería del barrio'
) ON CONFLICT (descripcion_item, cantidad, tienda_preferida) DO NOTHING;


-- ##################################################################################################################
-- # EJEMPLOS DE INSERCIÓN DE PEDIDOS Y SUS DETALLES (Comida, Paquete, Compra)                                      #
-- ##################################################################################################################

-- Ejemplo 1: Pedido de Comida
INSERT INTO pedidos (
    cliente_id,
    servicio_id,
    direccion_entrega_id,
    fecha_pedido,
    estado,
    total,
    costo_domicilio,
    notas,
    forma_pago_id
)
VALUES (
    (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1),
    (SELECT id FROM servicios WHERE nombre = 'comidas' LIMIT 1),
    (SELECT id FROM direcciones_cliente WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) LIMIT 1),
    CURRENT_TIMESTAMP - INTERVAL '1 hour', -- Hace 1 hora
    'entregado',
    29000.00, -- 21000 (Sushi) + 8000 (domicilio)
    8000.00,
    'Pedido de comida para la cena',
    (SELECT id FROM formas_pago WHERE nombre = 'efectivo' LIMIT 1)
) ON CONFLICT (cliente_id, fecha_pedido, total) DO NOTHING;

INSERT INTO detalles_pedido (
    pedido_id,
    tipo_item,
    producto_id,
    cantidad,
    precio_unitario
)
VALUES (
    (SELECT id FROM pedidos WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) AND servicio_id = (SELECT id FROM servicios WHERE nombre = 'comidas' LIMIT 1) ORDER BY fecha_pedido DESC LIMIT 1),
    'producto_comida',
    (SELECT id FROM productos WHERE nombre = 'Sushi00' LIMIT 1),
    1,
    21000.00
) ON CONFLICT (pedido_id, producto_id) DO NOTHING;

-- Ejemplo 2: Pedido de Paquete
INSERT INTO pedidos (
    cliente_id,
    servicio_id,
    direccion_entrega_id,
    fecha_pedido,
    estado,
    total,
    costo_domicilio,
    notas,
    forma_pago_id
)
VALUES (
    (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1),
    (SELECT id FROM servicios WHERE nombre = 'paquetes' LIMIT 1),
    (SELECT id FROM direcciones_cliente WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) LIMIT 1),
    CURRENT_TIMESTAMP - INTERVAL '30 minutes', -- Hace 30 minutos
    'pendiente',
    12000.00, -- Precio del paquete
    0.00, -- El costo ya está incluido en el precio calculado del paquete
    'Envío de documentos urgentes',
    (SELECT id FROM formas_pago WHERE nombre = 'nequi' LIMIT 1)
) ON CONFLICT (cliente_id, fecha_pedido, total) DO NOTHING;

INSERT INTO detalles_pedido (
    pedido_id,
    tipo_item,
    paquete_envio_id,
    cantidad,
    precio_unitario
)
VALUES (
    (SELECT id FROM pedidos WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) AND servicio_id = (SELECT id FROM servicios WHERE nombre = 'paquetes' LIMIT 1) ORDER BY fecha_pedido DESC LIMIT 1),
    'paquete_envio',
    (SELECT id FROM detalles_paquete_envio WHERE tipo_paquete = 'caja' AND descripcion LIKE '%Documentos importantes%' LIMIT 1),
    1,
    12000.00
) ON CONFLICT (pedido_id, paquete_envio_id) DO NOTHING;

-- Ejemplo 3: Pedido de Compras
INSERT INTO pedidos (
    cliente_id,
    servicio_id,
    direccion_entrega_id,
    fecha_pedido,
    estado,
    total,
    costo_domicilio,
    notas,
    forma_pago_id
)
VALUES (
    (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1),
    (SELECT id FROM servicios WHERE nombre = 'compras' LIMIT 1),
    (SELECT id FROM direcciones_cliente WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) LIMIT 1),
    CURRENT_TIMESTAMP - INTERVAL '15 minutes', -- Hace 15 minutos
    'en_camino',
    10000.00, -- Suma estimada de los ítems de compra + domicilio
    5000.00, -- Costo de domicilio para compras
    'Lista de mercado semanal',
    (SELECT id FROM formas_pago WHERE nombre = 'tarjeta de Crédito' LIMIT 1)
) ON CONFLICT (cliente_id, fecha_pedido, total) DO NOTHING;

INSERT INTO detalles_pedido (
    pedido_id,
    tipo_item,
    item_compra_id,
    cantidad,
    precio_unitario
)
VALUES (
    (SELECT id FROM pedidos WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) AND servicio_id = (SELECT id FROM servicios WHERE nombre = 'compras' LIMIT 1) ORDER BY fecha_pedido DESC LIMIT 1),
    'item_lista_compra',
    (SELECT id FROM detalles_item_compra WHERE descripcion_item = 'Leche entera Alpina 1L' LIMIT 1),
    2,
    3500.00 -- Precio unitario estimado
) ON CONFLICT (pedido_id, item_compra_id) DO NOTHING;

INSERT INTO detalles_pedido (
    pedido_id,
    tipo_item,
    item_compra_id,
    cantidad,
    precio_unitario
)
VALUES (
    (SELECT id FROM pedidos WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) AND servicio_id = (SELECT id FROM servicios WHERE nombre = 'compras' LIMIT 1) ORDER BY fecha_pedido DESC LIMIT 1),
    'item_lista_compra',
    (SELECT id FROM detalles_item_compra WHERE descripcion_item = 'Pan tajado Bimbo integral' LIMIT 1),
    1,
    5000.00 -- Precio unitario estimado
) ON CONFLICT (pedido_id, item_compra_id) DO NOTHING;


-- Ejemplo de historial de estados de pedido
INSERT INTO historial_estados_pedido (pedido_id, estado, fecha_cambio, usuario_cambio_id)
VALUES (
    (SELECT id FROM pedidos WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) AND servicio_id = (SELECT id FROM servicios WHERE nombre = 'comidas' LIMIT 1) ORDER BY fecha_pedido DESC LIMIT 1),
    'pendiente',
    CURRENT_TIMESTAMP - INTERVAL '1 hour 10 minutes',
    (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1)
) ON CONFLICT (pedido_id, estado, fecha_cambio) DO NOTHING;

INSERT INTO historial_estados_pedido (pedido_id, estado, fecha_cambio, usuario_cambio_id)
VALUES (
    (SELECT id FROM pedidos WHERE cliente_id = (SELECT id FROM usuarios WHERE email = 'Neiroc.700@gmail.com' LIMIT 1) AND servicio_id = (SELECT id FROM servicios WHERE nombre = 'comidas' LIMIT 1) ORDER BY fecha_pedido DESC LIMIT 1),
    'entregado',
    CURRENT_TIMESTAMP - INTERVAL '5 minutes',
    (SELECT id FROM motorizados WHERE email = 'prueba@gmail.com' LIMIT 1)
) ON CONFLICT (pedido_id, estado, fecha_cambio) DO NOTHING;

-- ##################################################################################################################
-- # FIN DEL SCRIPT                                                                                                 #
-- ##################################################################################################################
