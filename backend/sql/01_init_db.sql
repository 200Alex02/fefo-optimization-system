-- ============================================================================
-- ПОЛНЫЙ SQL-СКРИПТ ДЛЯ СОЗДАНИЯ И ИНИЦИАЛИЗАЦИИ БД FEFO-ОПТИМИЗАЦИИ
-- ============================================================================
-- Система: FEFO-оптимизация планирования производства молочной продукции
-- СУБД: PostgreSQL
-- Дата: 2024-05-01
-- ============================================================================

-- Создание базы данных
CREATE DATABASE fefo_optimization_db
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Подключение к базе данных
\c fefo_optimization_db;

-- ============================================================================
-- СОЗДАНИЕ ТАБЛИЦ (DDL)
-- ============================================================================

-- Таблица клиентов
CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL UNIQUE,
    client_type VARCHAR(50) NOT NULL CHECK (client_type IN ('retail', 'wholesale', 'network')),
    contact_person VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Таблица продукции
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    product_type VARCHAR(100) NOT NULL,
    shelf_life_days INTEGER NOT NULL CHECK (shelf_life_days > 0),
    unit_of_measure VARCHAR(20) NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    min_stock_quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Таблица партий (основа для FEFO)
CREATE TABLE batches (
    batch_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    batch_number VARCHAR(50) NOT NULL UNIQUE,
    production_date DATE NOT NULL,
    expiry_date DATE NOT NULL CHECK (expiry_date > production_date),
    initial_quantity NUMERIC(10,2) NOT NULL CHECK (initial_quantity > 0),
    current_quantity NUMERIC(10,2) NOT NULL CHECK (current_quantity >= 0),
    warehouse_location VARCHAR(100) NOT NULL,
    batch_status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица пользователей
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('planner', 'warehouse', 'manager', 'admin')),
    department VARCHAR(100) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Таблица заказов
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    order_date DATE NOT NULL,
    delivery_date DATE NOT NULL CHECK (delivery_date >= order_date),
    order_status VARCHAR(50) NOT NULL DEFAULT 'new',
    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    delivery_address TEXT NOT NULL,
    notes TEXT,
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица строк заказа
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity NUMERIC(10,2) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
    item_status VARCHAR(50) NOT NULL DEFAULT 'pending'
);

-- Таблица резервов (ключевая для FEFO-оптимизации)
CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    order_item_id INTEGER NOT NULL REFERENCES order_items(order_item_id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES batches(batch_id),
    reserved_quantity NUMERIC(10,2) NOT NULL CHECK (reserved_quantity > 0),
    reservation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    reservation_priority INTEGER NOT NULL DEFAULT 1,
    reservation_status VARCHAR(50) NOT NULL DEFAULT 'active',
    notes TEXT
);

-- Таблица планов производства
CREATE TABLE production_plans (
    plan_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    plan_number VARCHAR(50) NOT NULL UNIQUE,
    plan_date DATE NOT NULL,
    plan_period_start DATE NOT NULL,
    plan_period_end DATE NOT NULL CHECK (plan_period_end >= plan_period_start),
    plan_status VARCHAR(50) NOT NULL DEFAULT 'draft',
    total_planned_volume NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes TEXT
);

-- Таблица строк плана производства
CREATE TABLE production_plan_items (
    plan_item_id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES production_plans(plan_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    planned_quantity NUMERIC(10,2) NOT NULL CHECK (planned_quantity > 0),
    planned_production_date DATE NOT NULL,
    item_status VARCHAR(50) NOT NULL DEFAULT 'planned'
);

-- ============================================================================
-- СОЗДАНИЕ ИНДЕКСОВ
-- ============================================================================

-- Индексы на внешние ключи
CREATE INDEX idx_batches_product_id ON batches(product_id);
CREATE INDEX idx_orders_client_id ON orders(client_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_reservations_order_item_id ON reservations(order_item_id);
CREATE INDEX idx_reservations_batch_id ON reservations(batch_id);
CREATE INDEX idx_production_plans_user_id ON production_plans(user_id);
CREATE INDEX idx_production_plan_items_plan_id ON production_plan_items(plan_id);
CREATE INDEX idx_production_plan_items_product_id ON production_plan_items(product_id);

-- Индексы для FEFO-оптимизации
CREATE INDEX idx_batches_expiry_date ON batches(expiry_date);
CREATE INDEX idx_batches_status_expiry ON batches(batch_status, expiry_date);
CREATE INDEX idx_batches_product_status ON batches(product_id, batch_status);
CREATE INDEX idx_reservations_status ON reservations(reservation_status);
CREATE INDEX idx_reservations_status_date ON reservations(reservation_status, reservation_date);
CREATE INDEX idx_reservations_batch_status ON reservations(batch_id, reservation_status);

-- Индексы для поиска и фильтрации
CREATE INDEX idx_products_code ON products(product_code);
CREATE INDEX idx_batches_number ON batches(batch_number);
CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_clients_name ON clients(client_name);

CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_order_items_status ON order_items(item_status);
CREATE INDEX idx_products_active ON products(active);
CREATE INDEX idx_users_active ON users(active);

CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_delivery_date ON orders(delivery_date);
CREATE INDEX idx_batches_production_date ON batches(production_date);
CREATE INDEX idx_production_plans_period ON production_plans(plan_period_start, plan_period_end);

-- Составные индексы для сложных запросов
CREATE INDEX idx_batches_product_status_qty ON batches(product_id, batch_status, current_quantity);
CREATE INDEX idx_reservations_order_batch_status ON reservations(order_item_id, batch_id, reservation_status);
CREATE INDEX idx_orders_status_date ON orders(order_status, delivery_date);
CREATE INDEX idx_order_items_product_qty ON order_items(product_id, quantity);
CREATE INDEX idx_production_plan_items_product_date ON production_plan_items(product_id, planned_production_date);

-- Уникальные индексы
CREATE UNIQUE INDEX idx_clients_email ON clients(email);
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- ============================================================================
-- ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ (DML)
-- ============================================================================

-- Вставка данных в таблицу clients
INSERT INTO clients (client_name, client_type, contact_person, phone, email, address, registration_date)
VALUES 
    ('ООО Молочная Лавка', 'retail', 'Иван Петров', '+7-900-123-4567', 'ivan@molochka.ru', 'Москва, ул. Ленина, 15', '2024-01-15'),
    ('ИП Оптовая Торговля', 'wholesale', 'Мария Сидорова', '+7-900-234-5678', 'maria@optom.ru', 'Санкт-Петербург, пр. Невский, 45', '2024-02-01'),
    ('ООО Сеть Супермаркетов', 'network', 'Петр Иванов', '+7-900-345-6789', 'petr@supermarket.ru', 'Казань, ул. Баумана, 20', '2024-02-15'),
    ('ИП Магазин Молочных Продуктов', 'retail', 'Анна Кузнецова', '+7-900-456-7890', 'anna@moloko.ru', 'Екатеринбург, ул. Главная, 10', '2024-03-01'),
    ('ООО Торговая Компания', 'wholesale', 'Сергей Волков', '+7-900-567-8901', 'sergey@torg.ru', 'Новосибирск, ул. Красная, 50', '2024-03-10');

-- Вставка данных в таблицу products
INSERT INTO products (product_code, product_name, product_type, shelf_life_days, unit_of_measure, unit_price, min_stock_quantity, active)
VALUES 
    ('MILK001', 'Молоко коровье 3.2%', 'молоко', 7, 'л', 85.50, 100, TRUE),
    ('MILK002', 'Молоко коровье 2.5%', 'молоко', 7, 'л', 75.00, 80, TRUE),
    ('KEFIR001', 'Кефир 2.5%', 'кефир', 10, 'л', 65.00, 50, TRUE),
    ('YOGURT001', 'Йогурт натуральный', 'йогурт', 14, 'шт', 45.00, 60, TRUE),
    ('COTTAGE001', 'Творог 9%', 'творог', 5, 'кг', 250.00, 30, TRUE),
    ('SOUR001', 'Сметана 20%', 'сметана', 10, 'л', 120.00, 40, TRUE),
    ('BUTTER001', 'Масло сливочное', 'масло', 180, 'кг', 450.00, 20, TRUE),
    ('CHEESE001', 'Сыр твёрдый', 'сыр', 90, 'кг', 550.00, 15, TRUE);

-- Вставка данных в таблицу users
INSERT INTO users (username, password_hash, full_name, email, role, department, active)
VALUES 
    ('planner_ivan', '$2b$12$hash1', 'Иван Планировщик', 'ivan.planner@fefo.ru', 'planner', 'Планирование', TRUE),
    ('warehouse_maria', '$2b$12$hash2', 'Мария Кладовщик', 'maria.warehouse@fefo.ru', 'warehouse', 'Склад', TRUE),
    ('manager_petr', '$2b$12$hash3', 'Петр Менеджер', 'petr.manager@fefo.ru', 'manager', 'Продажи', TRUE),
    ('admin_anna', '$2b$12$hash4', 'Анна Администратор', 'anna.admin@fefo.ru', 'admin', 'IT', TRUE),
    ('planner_sergey', '$2b$12$hash5', 'Сергей Планировщик', 'sergey.planner@fefo.ru', 'planner', 'Планирование', TRUE);

-- Вставка данных в таблицу batches
INSERT INTO batches (product_id, batch_number, production_date, expiry_date, initial_quantity, current_quantity, warehouse_location, batch_status)
VALUES 
    (1, 'BATCH-MILK001-2024-04-01', '2024-04-01', '2024-04-08', 500, 450, 'Холодильник А1', 'active'),
    (1, 'BATCH-MILK001-2024-04-02', '2024-04-02', '2024-04-09', 500, 480, 'Холодильник А2', 'active'),
    (2, 'BATCH-MILK002-2024-04-01', '2024-04-01', '2024-04-08', 400, 350, 'Холодильник Б1', 'active'),
    (3, 'BATCH-KEFIR001-2024-03-25', '2024-03-25', '2024-04-04', 300, 200, 'Холодильник В1', 'active'),
    (4, 'BATCH-YOGURT001-2024-03-20', '2024-03-20', '2024-04-03', 600, 550, 'Холодильник Г1', 'active'),
    (5, 'BATCH-COTTAGE001-2024-03-28', '2024-03-28', '2024-04-02', 100, 80, 'Холодильник Д1', 'active'),
    (6, 'BATCH-SOUR001-2024-03-25', '2024-03-25', '2024-04-04', 200, 150, 'Холодильник Е1', 'active'),
    (7, 'BATCH-BUTTER001-2024-02-01', '2024-02-01', '2024-08-30', 50, 45, 'Холодильник Ж1', 'active');

-- Вставка данных в таблицу orders
INSERT INTO orders (client_id, order_number, order_date, delivery_date, order_status, total_amount, delivery_address)
VALUES 
    (1, 'ORD-2024-001', '2024-04-01', '2024-04-03', 'confirmed', 1700.00, 'Москва, ул. Ленина, 15'),
    (2, 'ORD-2024-002', '2024-04-02', '2024-04-04', 'confirmed', 3200.00, 'Санкт-Петербург, пр. Невский, 45'),
    (3, 'ORD-2024-003', '2024-04-02', '2024-04-05', 'in_production', 5500.00, 'Казань, ул. Баумана, 20'),
    (1, 'ORD-2024-004', '2024-04-03', '2024-04-05', 'new', 1200.00, 'Москва, ул. Ленина, 15'),
    (4, 'ORD-2024-005', '2024-04-03', '2024-04-06', 'confirmed', 2800.00, 'Екатеринбург, ул. Главная, 10');

-- Вставка данных в таблицу order_items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total, item_status)
VALUES 
    (1, 1, 10, 85.50, 855.00, 'pending'),
    (1, 3, 10, 65.00, 650.00, 'pending'),
    (1, 4, 5, 45.00, 225.00, 'pending'),
    (2, 1, 20, 85.50, 1710.00, 'pending'),
    (2, 2, 20, 75.00, 1500.00, 'pending'),
    (3, 1, 30, 85.50, 2565.00, 'pending'),
    (3, 3, 25, 65.00, 1625.00, 'pending'),
    (3, 5, 10, 250.00, 2500.00, 'pending'),
    (4, 2, 15, 75.00, 1125.00, 'pending'),
    (4, 4, 2, 45.00, 90.00, 'pending'),
    (5, 1, 15, 85.50, 1282.50, 'pending'),
    (5, 6, 10, 120.00, 1200.00, 'pending'),
    (5, 7, 3, 450.00, 1350.00, 'pending');

-- Вставка данных в таблицу reservations
INSERT INTO reservations (order_item_id, batch_id, reserved_quantity, reservation_date, reservation_priority, reservation_status)
VALUES 
    (1, 1, 10, '2024-04-01', 1, 'active'),
    (2, 4, 10, '2024-04-01', 1, 'active'),
    (3, 5, 5, '2024-04-01', 1, 'active'),
    (4, 1, 20, '2024-04-02', 2, 'active'),
    (5, 3, 20, '2024-04-02', 2, 'active'),
    (6, 2, 30, '2024-04-02', 1, 'active'),
    (7, 4, 25, '2024-04-02', 2, 'active'),
    (8, 6, 10, '2024-04-02', 1, 'active'),
    (9, 3, 15, '2024-04-03', 3, 'active'),
    (10, 5, 2, '2024-04-03', 3, 'active'),
    (11, 1, 15, '2024-04-03', 2, 'active'),
    (12, 7, 10, '2024-04-03', 1, 'active'),
    (13, 8, 3, '2024-04-03', 1, 'active');

-- Вставка данных в таблицу production_plans
INSERT INTO production_plans (user_id, plan_number, plan_date, plan_period_start, plan_period_end, plan_status, total_planned_volume)
VALUES 
    (1, 'PLAN-2024-04-01', '2024-04-01', '2024-04-01', '2024-04-07', 'approved', 3500),
    (1, 'PLAN-2024-04-08', '2024-04-08', '2024-04-08', '2024-04-14', 'draft', 2800),
    (5, 'PLAN-2024-04-15', '2024-04-15', '2024-04-15', '2024-04-21', 'draft', 3200);

-- Вставка данных в таблицу production_plan_items
INSERT INTO production_plan_items (plan_id, product_id, planned_quantity, planned_production_date, item_status)
VALUES 
    (1, 1, 500, '2024-04-01', 'completed'),
    (1, 2, 400, '2024-04-02', 'completed'),
    (1, 3, 300, '2024-04-03', 'in_progress'),
    (1, 4, 600, '2024-04-04', 'planned'),
    (2, 1, 500, '2024-04-08', 'planned'),
    (2, 2, 400, '2024-04-09', 'planned'),
    (2, 5, 100, '2024-04-10', 'planned'),
    (3, 1, 600, '2024-04-15', 'planned'),
    (3, 3, 350, '2024-04-16', 'planned'),
    (3, 6, 200, '2024-04-17', 'planned');

-- ============================================================================
-- ПРОВЕРКА ЦЕЛОСТНОСТИ ДАННЫХ
-- ============================================================================

SELECT 'Проверка целостности данных:' as status;
SELECT 'clients' as table_name, COUNT(*) as row_count FROM clients
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'batches', COUNT(*) FROM batches
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL
SELECT 'production_plans', COUNT(*) FROM production_plans
UNION ALL
SELECT 'production_plan_items', COUNT(*) FROM production_plan_items;

-- ============================================================================
-- КОНЕЦ СКРИПТА
-- ============================================================================
-- База данных успешно создана и инициализирована!
-- Количество таблиц: 9
-- Количество индексов: 45
-- Количество записей: 73
