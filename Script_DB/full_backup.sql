--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: transactiontype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.transactiontype AS ENUM (
    'DRIVER_RECHARGE',
    'COMMISSION_PAYMENT',
    'COMMISSION_EARNING',
    'CANCELLATION_PENALTY_DRIVER',
    'CANCELLATION_PENALTY_ADMIN'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: addresses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.addresses (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    address character varying(255) NOT NULL,
    alias character varying(100),
    is_principal boolean,
    latitud double precision,
    longitud double precision
);


--
-- Name: addresses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.addresses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: addresses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.addresses_id_seq OWNED BY public.addresses.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: business_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_categories (
    business_id integer NOT NULL,
    category_id integer NOT NULL
);


--
-- Name: business_payment_methods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_payment_methods (
    business_id integer NOT NULL,
    payment_method_id integer NOT NULL
);


--
-- Name: businesses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.businesses (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(120) NOT NULL,
    address character varying(255),
    phone_number character varying(20),
    description text,
    logo character varying(255),
    status character varying(20) DEFAULT 'Cerrado'::character varying,
    min_order_value double precision DEFAULT 0,
    delivery_fee double precision DEFAULT 0,
    average_delivery_time character varying(50),
    rating double precision DEFAULT 0.0,
    reviews_count integer DEFAULT 0,
    slug character varying(120) NOT NULL
);


--
-- Name: businesses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.businesses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: businesses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.businesses_id_seq OWNED BY public.businesses.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name character varying(80) NOT NULL,
    description text,
    image_url character varying(255)
);


--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    id integer NOT NULL,
    user_id integer NOT NULL,
    first_name character varying(60) NOT NULL,
    last_name character varying(60) NOT NULL,
    phone_number character varying(20),
    address character varying(255),
    profile_picture character varying(255),
    deuda_cancelacion numeric(10,2) NOT NULL
);


--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: detalles_item_compra; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalles_item_compra (
    id integer NOT NULL,
    descripcion_item text NOT NULL,
    cantidad integer NOT NULL,
    precio_estimado double precision,
    notas_especificas text,
    tienda_preferida character varying(255)
);


--
-- Name: detalles_item_compra_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalles_item_compra_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalles_item_compra_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalles_item_compra_id_seq OWNED BY public.detalles_item_compra.id;


--
-- Name: detalles_paquete_envio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalles_paquete_envio (
    id integer NOT NULL,
    tipo_paquete character varying(255) NOT NULL,
    tamano_paquete character varying(20),
    descripcion text,
    peso_kg double precision,
    dimensiones_cm character varying(50),
    valor_declarado double precision,
    instrucciones_especiales text,
    precio_calculado double precision NOT NULL
);


--
-- Name: detalles_paquete_envio_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalles_paquete_envio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalles_paquete_envio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalles_paquete_envio_id_seq OWNED BY public.detalles_paquete_envio.id;


--
-- Name: drivers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.drivers (
    id integer NOT NULL,
    user_id integer NOT NULL,
    first_name character varying(60) NOT NULL,
    last_name character varying(60) NOT NULL,
    phone_number character varying(20),
    vehicle_type character varying(50),
    license_plate character varying(20),
    is_available boolean DEFAULT true,
    current_location character varying(255),
    rating double precision DEFAULT 0.0,
    total_deliveries integer DEFAULT 0,
    profile_picture character varying(255),
    saldo_cuenta numeric(10,2) NOT NULL
);


--
-- Name: drivers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.drivers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: drivers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.drivers_id_seq OWNED BY public.drivers.id;


--
-- Name: historial_estados_pedido; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.historial_estados_pedido (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    estado character varying(50) NOT NULL,
    fecha_cambio timestamp without time zone,
    usuario_cambio_id integer
);


--
-- Name: historial_estados_pedido_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.historial_estados_pedido_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: historial_estados_pedido_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.historial_estados_pedido_id_seq OWNED BY public.historial_estados_pedido.id;


--
-- Name: opening_hours; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.opening_hours (
    id integer NOT NULL,
    business_id integer NOT NULL,
    day_of_week character varying(10) NOT NULL,
    open_time time without time zone NOT NULL,
    close_time time without time zone NOT NULL
);


--
-- Name: opening_hours_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.opening_hours_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: opening_hours_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.opening_hours_id_seq OWNED BY public.opening_hours.id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer,
    quantity integer NOT NULL,
    price_at_order double precision NOT NULL,
    tipo_item character varying(50) NOT NULL,
    paquete_envio_id integer,
    item_compra_id integer
);


--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    business_id integer,
    driver_id integer,
    delivery_address character varying(255) NOT NULL,
    total_amount double precision NOT NULL,
    status character varying(50) DEFAULT 'Pendiente'::character varying NOT NULL,
    user_id integer NOT NULL,
    servicio_id integer NOT NULL,
    order_date timestamp without time zone,
    costo_domicilio double precision,
    direccion_entrega_id integer,
    payment_status character varying(50) NOT NULL,
    payment_method_id integer,
    notes text,
    pickup_address character varying(255),
    direccion_recogida_id integer
);


--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: payment_methods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_methods (
    id integer NOT NULL,
    name character varying(80) NOT NULL,
    description text,
    is_active boolean
);


--
-- Name: payment_methods_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payment_methods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payment_methods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payment_methods_id_seq OWNED BY public.payment_methods.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    id integer NOT NULL,
    business_id integer NOT NULL,
    name character varying(120) NOT NULL,
    description text,
    price double precision NOT NULL,
    image_url character varying(255),
    is_available boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    category_id integer
);


--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: services; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.services (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text
);


--
-- Name: services_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.services_id_seq OWNED BY public.services.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    order_id integer,
    amount numeric(10,2) NOT NULL,
    type public.transactiontype NOT NULL,
    description character varying(255) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL
);


--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256) NOT NULL,
    role character varying(20) DEFAULT 'customer'::character varying NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: addresses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.addresses ALTER COLUMN id SET DEFAULT nextval('public.addresses_id_seq'::regclass);


--
-- Name: businesses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.businesses ALTER COLUMN id SET DEFAULT nextval('public.businesses_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: detalles_item_compra id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_item_compra ALTER COLUMN id SET DEFAULT nextval('public.detalles_item_compra_id_seq'::regclass);


--
-- Name: detalles_paquete_envio id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_paquete_envio ALTER COLUMN id SET DEFAULT nextval('public.detalles_paquete_envio_id_seq'::regclass);


--
-- Name: drivers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drivers ALTER COLUMN id SET DEFAULT nextval('public.drivers_id_seq'::regclass);


--
-- Name: historial_estados_pedido id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_estados_pedido ALTER COLUMN id SET DEFAULT nextval('public.historial_estados_pedido_id_seq'::regclass);


--
-- Name: opening_hours id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.opening_hours ALTER COLUMN id SET DEFAULT nextval('public.opening_hours_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: payment_methods id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_methods ALTER COLUMN id SET DEFAULT nextval('public.payment_methods_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: services id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.services ALTER COLUMN id SET DEFAULT nextval('public.services_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: addresses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.addresses (id, customer_id, address, alias, is_principal, latitud, longitud) FROM stdin;
1	4	Calle 37 11-80	Casa 1	f	\N	\N
2	4	Calle 100 10-10	Apartamento	f	\N	\N
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
ba9ba3ec963c
\.


--
-- Data for Name: business_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.business_categories (business_id, category_id) FROM stdin;
\.


--
-- Data for Name: business_payment_methods; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.business_payment_methods (business_id, payment_method_id) FROM stdin;
\.


--
-- Data for Name: businesses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.businesses (id, user_id, name, address, phone_number, description, logo, status, min_order_value, delivery_fee, average_delivery_time, rating, reviews_count, slug) FROM stdin;
1	7	Empanadas Yopal	Cra 20 10-25	3123495925	Las mejores empanadas de Yopal Casanare	\N	Abierto	0	0	\N	0	0	empanadas-yopal
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (id, name, description, image_url) FROM stdin;
1	Pizzas	\N	\N
2	Comida Rápida	\N	\N
3	Asiática	\N	\N
4	Vegetariana	\N	\N
5	Postres	\N	\N
6	Bebidas	\N	\N
7	Mercado	\N	\N
8	Farmacia	\N	\N
9	Otros	\N	\N
10	Tecnología	\N	\N
11	Belleza	\N	\N
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customers (id, user_id, first_name, last_name, phone_number, address, profile_picture, deuda_cancelacion) FROM stdin;
1	1	Pendiente	Pendiente	\N	\N	\N	0.00
2	2	Pendiente	Pendiente	\N	\N	\N	0.00
3	3	Pendiente	Pendiente	\N	\N	\N	0.00
5	5	sandita	Veez	3150000002	\N	\N	0.00
4	4	Pendiente	Pendiente	\N	\N	\N	53000.00
\.


--
-- Data for Name: detalles_item_compra; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.detalles_item_compra (id, descripcion_item, cantidad, precio_estimado, notas_especificas, tienda_preferida) FROM stdin;
\.


--
-- Data for Name: detalles_paquete_envio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.detalles_paquete_envio (id, tipo_paquete, tamano_paquete, descripcion, peso_kg, dimensiones_cm, valor_declarado, instrucciones_especiales, precio_calculado) FROM stdin;
4	caja_pequena	\N	Casco	6.01	10	10000	Rodado	0
5	documento	\N	Afiliaciones	3.01	20	20000	Radicar	0
6	otro	\N	Maleta verde	3.01	10	20000	Entregar señor camion	0
7	caja_pequena	\N	Saco	1.01	25	20000	Rojo casco	0
20	Gorron	pequeno	Gorra cafe	1.01	20	200000	Dejar gorra de prueba union	9000
21	Gorron moto	mediano	Gorron moto niño	1.01	20	25000	Entregar gorron moto niño uniom	7500
22	Bicicleta	grande	Biciclwta sin llantas	2.01	10	50000	Entregar en el taller	11000
23	Zapatillas	mediano	Zapatillas en caja	1.01	20	20000	Dejar en recepcion	7400
24	Gato	pequeno	Gato bebé	1.01	20	10000	Entregar a amo gato	5200
25	Boliche	mediano	fvffv	1.01	20	20000	gdfgd	7400
26	Bolso	pequeno	bolso amarillo	1.01	20	20000	Dejar en recepción bolso amarillo	5400
27	Bolso	pequeno	amarillo	1.01	20	2000	Dejar en recepción bolso amarillo	5040
28	Bolso	pequeno	Bolso amarillo	1.01	20	50000	Bolso amarillo dejar en recepción	6000
29	Computador	pequeno	Portatil	1.01	20	20000	Negro portatil computador	5400
30	Computador	pequeno	Portatil	1.01	20	20000	Negro portatil computador	5400
31	Nevera	mediano	Nevera gris	1.01	20	20000	Nevera gris conjunto	7400
32	Microondas	mediano	Microondas negro	1.01	20	100000	Microondas negro timbrar en segundo piso	9000
33	Microondas	mediano	Microondas negro	1.01	20	200000	Microondas negro recepción	11000
34	Mouse	pequeno	Mouse negro	1.01	20	10000	Mouse negro aparta	5200
35	Detalle	pequeno	Oso peluche	1.01	20	10000	Entregar oso a Lozada	5200
36	Balon	pequeno	Pecoza	1.01	20	20000	Dejar en puerta pecoza	5400
37	Oso peluche	grande	Peluchote	1.01	20	20000	oso peluche bos	10400
\.


--
-- Data for Name: drivers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.drivers (id, user_id, first_name, last_name, phone_number, vehicle_type, license_plate, is_available, current_location, rating, total_deliveries, profile_picture, saldo_cuenta) FROM stdin;
2	8	nn	nnb	2154654544	Carro	ACR65T	f	\N	0	0	\N	0.00
1	6	prueba	motorizado	3123495918	Motocicleta	MOK25F	t	\N	0	0	\N	31300.00
\.


--
-- Data for Name: historial_estados_pedido; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.historial_estados_pedido (id, pedido_id, estado, fecha_cambio, usuario_cambio_id) FROM stdin;
\.


--
-- Data for Name: opening_hours; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.opening_hours (id, business_id, day_of_week, open_time, close_time) FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_items (id, order_id, product_id, quantity, price_at_order, tipo_item, paquete_envio_id, item_compra_id) FROM stdin;
1	1	1	1	3000	producto_comida	\N	\N
2	2	1	2	3000	producto_comida	\N	\N
3	3	1	3	3000	producto_comida	\N	\N
4	4	1	4	3000	producto_comida	\N	\N
5	5	1	2	3000	producto_comida	\N	\N
6	6	1	5	3000	producto_comida	\N	\N
7	7	1	8	3000	producto_comida	\N	\N
8	8	1	1	3000	producto_comida	\N	\N
9	9	1	1	3000	producto_comida	\N	\N
10	10	1	1	3000	producto_comida	\N	\N
11	11	1	4	3000	producto_comida	\N	\N
12	12	1	2	3000	producto_comida	\N	\N
13	13	1	15	3000	producto_comida	\N	\N
14	14	1	2	3000	producto_comida	\N	\N
15	15	1	1	3000	producto_comida	\N	\N
16	17	1	3	3000	producto_comida	\N	\N
17	18	1	4	3000	producto_comida	\N	\N
18	19	1	1	3000	producto_comida	\N	\N
19	20	1	2	3000	producto_comida	\N	\N
20	21	1	1	3000	producto_comida	\N	\N
21	22	1	1	3000	producto_comida	\N	\N
22	23	1	2	3000	producto_comida	\N	\N
23	24	1	3	3000	producto_comida	\N	\N
24	25	1	2	3000	producto_comida	\N	\N
25	29	1	2	3000	producto_comida	\N	\N
26	35	1	2	3000	producto_comida	\N	\N
27	36	\N	1	11000	paquete_envio	22	\N
28	37	1	1	3000	producto_comida	\N	\N
29	38	1	1	3000	producto_comida	\N	\N
30	39	1	1	3000	producto_comida	\N	\N
31	40	1	3	3000	producto_comida	\N	\N
32	41	1	2	3000	producto_comida	\N	\N
33	42	1	2	3000	producto_comida	\N	\N
34	43	1	2	3000	producto_comida	\N	\N
35	44	1	3	3000	producto_comida	\N	\N
36	45	1	5	3000	producto_comida	\N	\N
37	46	1	1	3000	producto_comida	\N	\N
38	47	\N	1	5200	paquete_envio	24	\N
39	48	1	8	3000	producto_comida	\N	\N
40	49	1	4	3000	producto_comida	\N	\N
41	50	1	3	3000	producto_comida	\N	\N
42	51	\N	1	7400	paquete_envio	25	\N
43	52	1	2	3000	producto_comida	\N	\N
44	53	1	1	3000	producto_comida	\N	\N
45	54	\N	1	5200	paquete_envio	35	\N
46	55	1	2	3000	producto_comida	\N	\N
47	56	1	1	3000	producto_comida	\N	\N
48	57	1	2	3000	producto_comida	\N	\N
49	58	\N	1	5400	paquete_envio	36	\N
50	59	1	1	3000	producto_comida	\N	\N
51	60	1	2	3000	producto_comida	\N	\N
52	61	1	3	3000	producto_comida	\N	\N
53	62	\N	1	10400	paquete_envio	37	\N
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orders (id, business_id, driver_id, delivery_address, total_amount, status, user_id, servicio_id, order_date, costo_domicilio, direccion_entrega_id, payment_status, payment_method_id, notes, pickup_address, direccion_recogida_id) FROM stdin;
29	1	\N	Apartamento: Calle 100 10-10	6000	Pendiente	4	1	2025-06-11 00:54:02.760547	0	2	Pendiente	5	Prueba después de paquete	\N	\N
1	1	\N	Calle 37 11-80	3000	Entregado	4	1	2025-06-05 06:28:40.801154	0	1	Pendiente	6	Timbrar segundo piso, ventana roja	\N	\N
4	1	\N	Calle 37 11-80	12000	Entregado	4	1	2025-06-05 06:44:19.632991	0	1	Pendiente	6	No olvides las gaseosas	\N	\N
30	1	\N	Casa 1: Calle 37 11-80	0	Pendiente	4	1	2025-06-11 03:08:45.012561	0	1	Pendiente	1	Este pedido va incompleto	\N	\N
3	1	\N	Calle 37 11-80	9000	Entregado	4	1	2025-06-05 06:39:10.849285	0	1	Pendiente	6	Enviar número nequi para enviar dinero	\N	\N
2	1	1	Calle 37 11-80	6000	Entregado	4	1	2025-06-05 06:36:14.748829	0	1	Pendiente	6	Llevar vueltas para un billete de 20 mil	\N	\N
5	1	1	Calle 37 11-80	6000	Entregado	4	1	2025-06-06 04:55:38.463788	0	1	Pendiente	7	Rapicredito	\N	\N
7	1	\N	Calle 37 11-80	24000	Pendiente	4	1	2025-06-06 16:22:00.765237	0	1	Pendiente	6	prueba restablecimiento	\N	\N
8	1	\N	Calle 37 11-80	3000	Pendiente	4	1	2025-06-06 17:32:43.660807	0	1	Pendiente	6	Reestablecimiento de carro, segundo ppiso	\N	\N
9	1	\N	Calle 37 11-80	3000	Pendiente	4	1	2025-06-06 19:57:53.270908	0	1	Pendiente	6	reestablecimiento 2	\N	\N
10	1	\N	Calle 37 11-80	3000	Pendiente	4	1	2025-06-06 20:03:37.987666	0	1	Pendiente	6	reestablecimeitno 3	\N	\N
11	1	\N	Calle 37 11-80	12000	Pendiente	4	1	2025-06-06 20:11:10.966554	0	1	Pendiente	6	Dejar en casa, restab 4	\N	\N
12	1	\N	Calle 37 11-80	6000	Pendiente	4	1	2025-06-06 20:14:29.440432	0	1	Pendiente	6	Reest 5	\N	\N
13	1	\N	Calle 37 11-80	45000	Pendiente	4	1	2025-06-06 20:32:06.575263	0	1	Pendiente	7	Solución carrito, golpear duro	\N	\N
14	1	\N	Calle 37 11-80	6000	Pendiente	4	1	2025-06-06 20:37:08.993156	0	1	Pendiente	6	rees car	\N	\N
15	1	1	Calle 37 11-80	3000	Entregado	4	1	2025-06-06 20:39:27.717218	0	1	Pendiente	6		\N	\N
16	1	\N	Apartamento: Calle 100 10-10	0	Pendiente	4	1	2025-06-09 19:32:23.17455	0	2	Pendiente	3	prueba 3	\N	\N
17	1	\N	Casa 1: Calle 37 11-80	9000	Pendiente	4	1	2025-06-09 22:25:30.873901	0	1	Pendiente	1	Prueba precio producto	\N	\N
18	1	\N	Casa 1: Calle 37 11-80	12000	Pendiente	4	1	2025-06-09 22:42:52.478496	0	1	Pendiente	1	Prueba4	\N	\N
19	1	\N	Casa 1: Calle 37 11-80	3000	Pendiente	4	1	2025-06-09 23:05:11.385111	0	1	Pendiente	1	prueba limpiar	\N	\N
20	1	\N	Apartamento: Calle 100 10-10	6000	Pendiente	4	1	2025-06-09 23:14:41.390867	0	2	Pendiente	3	Traer datafono	\N	\N
21	1	\N	Casa 1: Calle 37 11-80	3000	Pendiente	4	1	2025-06-09 23:17:14.957305	0	1	Pendiente	1	Prueba borrado	\N	\N
22	1	\N	Casa 1: Calle 37 11-80	3000	Pendiente	4	1	2025-06-09 23:20:47.619078	0	1	Pendiente	1		\N	\N
23	1	\N	Casa 1: Calle 37 11-80	6000	Pendiente	4	1	2025-06-09 23:22:28.166645	0	1	Pendiente	1	Para la abuela y el abuelo	\N	\N
24	1	\N	Apartamento: Calle 100 10-10	9000	Pendiente	4	1	2025-06-09 23:36:16.398839	0	2	Pendiente	4	Dejar en recepción. Enviar número de nequi para pagarle anticipadamente.	\N	\N
6	1	1	Calle 37 11-80	15000	Entregado	4	1	2025-06-06 13:31:51.372374	0	1	Pendiente	6	Historial	\N	\N
35	1	\N	Casa 1: Calle 37 11-80	0	Pendiente	4	1	2025-06-12 04:47:54.223434	0	1	Pendiente	6	Prueba union	\N	\N
36	\N	\N	1	11000	Pendiente	4	2	2025-06-12 05:33:54.455047	0	2	Pendiente	6	Enviar número nequi al dejat en taller	\N	\N
38	1	1	Casa 1: Calle 37 11-80	3000	Entregado	4	1	2025-06-12 15:47:57.940675	0	1	Pendiente	6		\N	\N
28	1	1	Casa 1: Calle 37 11-80	0	Entregado	4	1	2025-06-11 00:46:32.832882	0	1	Pendiente	1	fdgfdb	\N	\N
43	1	1	Casa 1: Calle 37 11-80	6000	Aceptado	4	1	2025-06-14 15:38:07.141092	0	1	Pendiente	6	Nequi efectivo	\N	\N
37	1	1	Apartamento: Calle 100 10-10	3000	Aceptado	4	1	2025-06-12 05:37:15.112818	0	2	Pendiente	6	Empanadas union paquetes	\N	\N
39	1	1	Casa 1: Calle 37 11-80	3000	Entregado	4	1	2025-06-14 00:03:24.035493	10000	1	Pendiente	6	Dejar en recepción	\N	\N
41	1	1	Casa 1: Calle 37 11-80	6000	Entregado	4	1	2025-06-14 00:31:54.306508	15000	1	Pendiente	6	Domicilio	\N	\N
40	1	1	Apartamento: Calle 100 10-10	9000	Entregado	4	1	2025-06-14 00:18:37.742583	20000	2	Pendiente	7	Descontar de base motorizado	\N	\N
42	1	1	Casa 1: Calle 37 11-80	6000	Aceptado	4	1	2025-06-14 03:45:44.272757	0	1	Pendiente	6		\N	\N
25	1	1	Casa 1: Calle 37 11-80	6000	Aceptado	4	1	2025-06-10 04:42:25.049141	11000	1	Pendiente	5	Pago daviplata pack carr	\N	\N
44	1	1	Apartamento: Calle 100 10-10	9000	Entregado	4	1	2025-06-14 15:51:22.29573	0	2	Pendiente	6	solo monedas costo domi	\N	\N
45	1	1	Apartamento: Calle 100 10-10	15000	Entregado	4	1	2025-06-14 16:01:48.246394	11000	2	Pendiente	7	Traer datafono cuenta conductor ganancia domi	\N	\N
46	1	1	Apartamento: Calle 100 10-10	3000	Aceptado	4	1	2025-06-14 16:50:57.237483	20000	2	Pendiente	7	Traer datáfono, pago con tarjeta domicilio	\N	\N
47	\N	\N	2	5200	Cancelado	4	2	2025-06-14 16:56:54.457885	0	1	Pendiente	6	Entregar a amo 2 gato	\N	\N
49	1	1	Casa 1: Calle 37 11-80	12000	Cancelado	4	1	2025-06-14 17:34:01.568425	30000	1	Pendiente	6	Prueba cancelacion cuota	\N	\N
48	1	1	Casa 1: Calle 37 11-80	24000	Cancelado	4	1	2025-06-14 17:25:35.603801	10000	1	Pendiente	6	pedido cancelado con penal	\N	\N
50	1	1	Apartamento: Calle 100 10-10	9000	Cancelado	4	1	2025-06-14 18:54:51.779204	8000	2	Pendiente	6	Traer todo lo solicitado a tiempo	\N	\N
51	\N	\N	2	7400	Pendiente	4	2	2025-06-14 19:29:42.70855	0	1	Pendiente	6	Entrega boliche	\N	\N
52	1	\N	Casa 1: Calle 37 11-80	6000	Cancelado	4	1	2025-06-16 12:13:58.288368	0	1	Pendiente	6	Entregar segundo piso	\N	\N
53	1	1	Apartamento: Calle 100 10-10	3000	Cancelado	4	1	2025-06-16 12:22:37.885714	7000	2	Pendiente	6	Entregar guarda seguridad Lozada	\N	\N
55	1	1	Casa 1: Calle 37 11-80	6000	Entregado	4	1	2025-06-16 14:16:22.194412	10000	1	Pendiente	6	Pedido transaccional	\N	\N
56	1	\N	Casa 1: Calle 37 11-80	3000	Cancelado	4	1	2025-06-16 15:06:45.499857	0	1	Pendiente	6	Dejar en sala	\N	\N
57	1	\N	Casa 1: Calle 37 11-80	6000	Cancelado	4	1	2025-06-16 15:07:20.772349	0	1	Pendiente	6	Dejar en mesa sala	\N	\N
58	\N	1	Apartamento: Calle 100 10-10	5400	Cancelado	4	2	2025-06-16 15:21:57.215584	6000	2	Pendiente	6	Dejar ahí pecoza	Casa 1: Calle 37 11-80	1
59	1	\N	Casa 1: Calle 37 11-80	3000	Cancelado	4	1	2025-06-16 18:04:24.202958	0	1	Pendiente	6	Prueba penalización sin conductor	\N	\N
60	1	1	Casa 1: Calle 37 11-80	6000	Cancelado	4	1	2025-06-16 18:06:32.456944	10000	1	Pendiente	6	Prueba exitosa ganancia	\N	\N
61	1	\N	Casa 1: Calle 37 11-80	9000	Cancelado	4	1	2025-06-16 18:20:42.928553	0	1	Pendiente	6	Pedido administrador	\N	\N
54	\N	1	Apartamento: Calle 100 10-10	5200	Entregado	4	2	2025-06-16 12:36:38.63398	10000	2	Pendiente	6	Entregar oso a Lozada, guarda seguridad	Casa 1: Calle 37 11-80	1
62	\N	1	Casa 1: Calle 37 11-80	10400	Entregado	4	2	2025-06-17 01:48:35.142901	10000	1	Pendiente	6	Entrega peluche	Apartamento: Calle 100 10-10	2
\.


--
-- Data for Name: payment_methods; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payment_methods (id, name, description, is_active) FROM stdin;
1	Efectivo	\N	\N
2	Tarjeta (online)	\N	\N
3	Datafono	\N	\N
4	Nequi	\N	\N
5	Daviplata	\N	\N
6	efectivo	Pago en efectivo al motorizado	t
7	tarjeta de Crédito	Pago con tarjeta de crédito	t
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.products (id, business_id, name, description, price, image_url, is_available, created_at, updated_at, category_id) FROM stdin;
1	1	Pasteles de yuca	Combo con vaso de gaseosa	3000	https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR2P71gYMNwxWOqNUP6HWiN2GN_sGSmWOhd6A&s	t	2025-06-04 18:26:52.127006	2025-06-04 18:26:52.127006	2
\.


--
-- Data for Name: services; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.services (id, name, description) FROM stdin;
1	comidas	Servicio de entrega de alimentos
2	paquetes	Envío y recogida de paquetes
3	compras	Servicio para realizar compras
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transactions (id, user_id, order_id, amount, type, description, "timestamp") FROM stdin;
1	6	55	-2000.00	COMMISSION_PAYMENT	Pago de comisión del 20% por pedido #55	2025-06-16 14:20:17.533611
2	9	55	2000.00	COMMISSION_EARNING	Ganancia de comisión del 20% por pedido #55	2025-06-16 14:20:17.533611
3	6	58	3000.00	CANCELLATION_PENALTY_DRIVER	Compensación por cancelación de pedido #58	2025-06-16 17:57:29.933959
4	9	58	3000.00	CANCELLATION_PENALTY_ADMIN	Ganancia por cancelación de pedido #58	2025-06-16 17:57:29.933959
5	6	60	5000.00	CANCELLATION_PENALTY_DRIVER	Compensación por cancelación de pedido #60	2025-06-16 18:19:53.683853
6	9	60	5000.00	CANCELLATION_PENALTY_ADMIN	Ganancia por cancelación de pedido #60	2025-06-16 18:19:53.683853
7	9	61	2000.00	CANCELLATION_PENALTY_ADMIN	Ganancia por cancelación de pedido #61	2025-06-16 18:30:27.59816
8	6	53	3500.00	CANCELLATION_PENALTY_DRIVER	Compensación por cancelación de pedido #53	2025-06-16 18:36:19.108839
9	9	53	3500.00	CANCELLATION_PENALTY_ADMIN	Ganancia por cancelación de pedido #53	2025-06-16 18:36:19.108839
10	6	54	-2000.00	COMMISSION_PAYMENT	Pago de comisión del 20% por pedido #54	2025-06-16 18:52:35.475494
11	9	54	2000.00	COMMISSION_EARNING	Ganancia de comisión del 20% por pedido #54	2025-06-16 18:52:35.475494
12	6	62	-2000.00	COMMISSION_PAYMENT	Pago de comisión del 20% por pedido #62	2025-06-17 18:02:27.09395
13	9	62	2000.00	COMMISSION_EARNING	Ganancia de comisión del 20% por pedido #62	2025-06-17 18:02:27.09395
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, password_hash, role, is_active, created_at, updated_at) FROM stdin;
2	jorge@gmail.com	scrypt:32768:8:1$o1pR2mSyQmsckEPE$19cee7a9e7b2304b06731cfd6e9b8025227fb05950e36e7d8e284835a9778d94f3febb9fa4903e41e45184ec3455d29356b9b625dbccf0737ce0a73e7f239c7c	customer	t	2025-06-02 05:24:23.591649	2025-06-02 05:24:23.591649
3	ana@gmail.com	scrypt:32768:8:1$W9vrTxIn8ubtikLm$16678f7573b4a49a3cddb02cd57d48da20dfd4bb4c210677e5748c0b62541b74578428c3a64edb9c1e8874b368f3e329cf9abbb43429ded27ff9a1709fa66e59	customer	t	2025-06-02 05:39:29.726332	2025-06-02 05:39:29.726332
7	empanadas@gmail.com	scrypt:32768:8:1$4wjROSXkisv9aExF$4b41dd21630e83cd072f962453a9cf1f9d7f1f959003f63f1a126e7969a4441d73b1ae74d9c27ae5fa9ee55f67b627648a387657801cd04dc2d9407aeeec8448	business	t	2025-06-04 02:40:51.205979	2025-06-09 05:38:54.113021
4	Neiroc.7@gmail.com	scrypt:32768:8:1$crjIWfIbn6pfbcm2$d60e466ee7eed3f5fce2e04732d8ec1528f18d050ef79999d9c439aec3d549dca31cb39947452e395cc0f8c129ad7ca12f9890037777faf929520bc177812044	customer	t	2025-06-02 06:05:42.052561	2025-06-03 08:03:01.268434
5	sandita@gmail.com	scrypt:32768:8:1$GEFgbeYZUx6OwBUl$57fc7f6b4f5494ccee76f5774248c00bca720889d8dd6e7e1b224c068f277bd159eaf33b5fd47367e7289b0befb744857f1843ad4060015eb6862c0cc4de008a	customer	t	2025-06-04 00:32:43.24008	2025-06-04 00:32:43.24008
6	Neiroc.702@gmail.com	scrypt:32768:8:1$SxjU6wMWB6xyclJL$fece8c5381e4ffcef4522a6feedf8ee8622ca89f6bf93a4fd04ab1ce14dabf9a320190bac4ec6ec37c9f74ac4cf4bc7e5f0d270a861a590736ca13a97bf19573	driver	t	2025-06-04 01:45:47.365484	2025-06-04 01:45:47.365484
8	Neiroc.15@gmail.com	scrypt:32768:8:1$tsUv4WdhPQG1L7bA$d939b261b41818a093795e03210273359999c1196c3803e0834044cbd9c7d593a4092071db6493b5c859684d87df3f7440e90c31a80b81c661c77194e20cffe1	driver	f	2025-06-04 04:05:30.382475	2025-06-12 16:17:54.862135
9	nculmay@ucentral.edu.co	scrypt:32768:8:1$G2mQhwNvxgdn56kz$9b85390874bd2d45396122b973fa543ba581b25c38f2382c4da122d299a7cf8c652f77d3b167df32e16a3185aed106082d58434d214341024ef5d77041e4cb52	admin	t	2025-06-06 04:05:30.382475	2025-06-06 22:53:09.025299
1	laura@gmail.com	scrypt:32768:8:1$05EwAcnjiOIN7faS$28193f1eb19f2e68747b284f7a68ae0d364e8764e5cb271dfad37540e7ff7e3b4c06b197243e42b134d9706bc7bb77acf5b6ae75290faff8eb1ddca2421433e8	customer	f	2025-06-02 05:13:45.558329	2025-06-09 05:38:38.554099
\.


--
-- Name: addresses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.addresses_id_seq', 2, true);


--
-- Name: businesses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.businesses_id_seq', 1, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.categories_id_seq', 11, true);


--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.customers_id_seq', 5, true);


--
-- Name: detalles_item_compra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.detalles_item_compra_id_seq', 1, false);


--
-- Name: detalles_paquete_envio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.detalles_paquete_envio_id_seq', 37, true);


--
-- Name: drivers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.drivers_id_seq', 2, true);


--
-- Name: historial_estados_pedido_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_estados_pedido_id_seq', 1, false);


--
-- Name: opening_hours_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.opening_hours_id_seq', 1, false);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.order_items_id_seq', 53, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orders_id_seq', 62, true);


--
-- Name: payment_methods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payment_methods_id_seq', 7, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.products_id_seq', 1, true);


--
-- Name: services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.services_id_seq', 3, true);


--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.transactions_id_seq', 13, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 9, true);


--
-- Name: addresses addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: business_categories business_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_categories
    ADD CONSTRAINT business_categories_pkey PRIMARY KEY (business_id, category_id);


--
-- Name: business_payment_methods business_payment_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_payment_methods
    ADD CONSTRAINT business_payment_methods_pkey PRIMARY KEY (business_id, payment_method_id);


--
-- Name: businesses businesses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_pkey PRIMARY KEY (id);


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: customers customers_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_phone_number_key UNIQUE (phone_number);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: detalles_item_compra detalles_item_compra_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_item_compra
    ADD CONSTRAINT detalles_item_compra_pkey PRIMARY KEY (id);


--
-- Name: detalles_paquete_envio detalles_paquete_envio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_paquete_envio
    ADD CONSTRAINT detalles_paquete_envio_pkey PRIMARY KEY (id);


--
-- Name: drivers drivers_license_plate_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_license_plate_key UNIQUE (license_plate);


--
-- Name: drivers drivers_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_phone_number_key UNIQUE (phone_number);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (id);


--
-- Name: historial_estados_pedido historial_estados_pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_estados_pedido
    ADD CONSTRAINT historial_estados_pedido_pkey PRIMARY KEY (id);


--
-- Name: opening_hours opening_hours_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.opening_hours
    ADD CONSTRAINT opening_hours_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payment_methods payment_methods_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_name_key UNIQUE (name);


--
-- Name: payment_methods payment_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: services services_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_name_key UNIQUE (name);


--
-- Name: services services_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_businesses_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_businesses_slug ON public.businesses USING btree (slug);


--
-- Name: ix_businesses_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_businesses_status ON public.businesses USING btree (status);


--
-- Name: ix_businesses_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_businesses_user_id ON public.businesses USING btree (user_id);


--
-- Name: ix_customers_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_customers_user_id ON public.customers USING btree (user_id);


--
-- Name: ix_drivers_is_available; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_drivers_is_available ON public.drivers USING btree (is_available);


--
-- Name: ix_drivers_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_drivers_user_id ON public.drivers USING btree (user_id);


--
-- Name: ix_opening_hours_business_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_opening_hours_business_id ON public.opening_hours USING btree (business_id);


--
-- Name: ix_order_items_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_order_items_order_id ON public.order_items USING btree (order_id);


--
-- Name: ix_orders_business_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_business_id ON public.orders USING btree (business_id);


--
-- Name: ix_orders_driver_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_driver_id ON public.orders USING btree (driver_id);


--
-- Name: ix_orders_servicio_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_servicio_id ON public.orders USING btree (servicio_id);


--
-- Name: ix_orders_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_user_id ON public.orders USING btree (user_id);


--
-- Name: ix_products_business_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_products_business_id ON public.products USING btree (business_id);


--
-- Name: ix_transactions_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_order_id ON public.transactions USING btree (order_id);


--
-- Name: ix_transactions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_user_id ON public.transactions USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_role ON public.users USING btree (role);


--
-- Name: addresses addresses_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: business_categories business_categories_business_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_categories
    ADD CONSTRAINT business_categories_business_id_fkey FOREIGN KEY (business_id) REFERENCES public.businesses(id) ON DELETE CASCADE;


--
-- Name: business_categories business_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_categories
    ADD CONSTRAINT business_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: business_payment_methods business_payment_methods_business_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_payment_methods
    ADD CONSTRAINT business_payment_methods_business_id_fkey FOREIGN KEY (business_id) REFERENCES public.businesses(id) ON DELETE CASCADE;


--
-- Name: business_payment_methods business_payment_methods_payment_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_payment_methods
    ADD CONSTRAINT business_payment_methods_payment_method_id_fkey FOREIGN KEY (payment_method_id) REFERENCES public.payment_methods(id) ON DELETE CASCADE;


--
-- Name: businesses businesses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: customers customers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: drivers drivers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: historial_estados_pedido historial_estados_pedido_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_estados_pedido
    ADD CONSTRAINT historial_estados_pedido_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.orders(id);


--
-- Name: historial_estados_pedido historial_estados_pedido_usuario_cambio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_estados_pedido
    ADD CONSTRAINT historial_estados_pedido_usuario_cambio_id_fkey FOREIGN KEY (usuario_cambio_id) REFERENCES public.users(id);


--
-- Name: opening_hours opening_hours_business_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.opening_hours
    ADD CONSTRAINT opening_hours_business_id_fkey FOREIGN KEY (business_id) REFERENCES public.businesses(id) ON DELETE CASCADE;


--
-- Name: order_items order_items_item_compra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_item_compra_id_fkey FOREIGN KEY (item_compra_id) REFERENCES public.detalles_item_compra(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: order_items order_items_paquete_envio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_paquete_envio_id_fkey FOREIGN KEY (paquete_envio_id) REFERENCES public.detalles_paquete_envio(id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: orders orders_business_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_business_id_fkey FOREIGN KEY (business_id) REFERENCES public.businesses(id);


--
-- Name: orders orders_direccion_entrega_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_direccion_entrega_id_fkey FOREIGN KEY (direccion_entrega_id) REFERENCES public.addresses(id);


--
-- Name: orders orders_direccion_recogida_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_direccion_recogida_id_fkey FOREIGN KEY (direccion_recogida_id) REFERENCES public.addresses(id);


--
-- Name: orders orders_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(id);


--
-- Name: orders orders_payment_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_payment_method_id_fkey FOREIGN KEY (payment_method_id) REFERENCES public.payment_methods(id);


--
-- Name: orders orders_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.services(id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: products products_business_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_business_id_fkey FOREIGN KEY (business_id) REFERENCES public.businesses(id) ON DELETE CASCADE;


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: transactions transactions_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

