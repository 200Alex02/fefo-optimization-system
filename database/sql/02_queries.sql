-- ============================================================================
-- ПРИМЕРЫ ЗАПРОСОВ К БАЗЕ ДАННЫХ FEFO-ОПТИМИЗАЦИИ
-- ============================================================================

-- 1. Общий объём заказов по клиентам (с SUM, COUNT, AVG)
SELECT 
    c.client_id,
    c.client_name,
    c.client_type,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(o.total_amount) as total_sales,
    AVG(o.total_amount) as avg_order_amount
FROM clients c
LEFT JOIN orders o ON c.client_id = o.client_id
GROUP BY c.client_id, c.client_name, c.client_type
ORDER BY total_sales DESC;

-- 2. Анализ остатков продукции по складам (с SUM, COUNT)
SELECT 
    p.product_id,
    p.product_name,
    p.product_type,
    p.min_stock_quantity,
    COUNT(DISTINCT b.batch_id) as total_batches,
    SUM(b.current_quantity) as total_stock,
    SUM(r.reserved_quantity) as total_reserved,
    SUM(b.current_quantity) - COALESCE(SUM(r.reserved_quantity), 0) as available_stock,
    CASE 
        WHEN SUM(b.current_quantity) < p.min_stock_quantity THEN 'ДЕФИЦИТ'
        WHEN SUM(b.current_quantity) < p.min_stock_quantity * 1.5 THEN 'НИЗКИЙ'
        ELSE 'НОРМАЛЬНЫЙ'
    END as stock_status
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id AND b.batch_status = 'active'
LEFT JOIN reservations r ON b.batch_id = r.batch_id AND r.reservation_status = 'active'
WHERE p.active = TRUE
GROUP BY p.product_id, p.product_name, p.product_type, p.min_stock_quantity
ORDER BY stock_status DESC, available_stock ASC;

-- 3. Статистика по партиям, близким к истечению срока (с COUNT, MIN)
SELECT 
    b.batch_id,
    b.batch_number,
    p.product_name,
    b.production_date,
    b.expiry_date,
    EXTRACT(DAY FROM b.expiry_date - CURRENT_DATE) as days_to_expiry,
    b.current_quantity,
    COUNT(r.reservation_id) as reservation_count,
    SUM(r.reserved_quantity) as total_reserved,
    b.current_quantity - COALESCE(SUM(r.reserved_quantity), 0) as unreserved_quantity,
    MIN(o.delivery_date) as earliest_delivery_date
FROM batches b
JOIN products p ON b.product_id = p.product_id
LEFT JOIN reservations r ON b.batch_id = r.batch_id AND r.reservation_status = 'active'
LEFT JOIN order_items oi ON r.order_item_id = oi.order_item_id
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE b.batch_status = 'active' 
    AND b.expiry_date <= CURRENT_DATE + INTERVAL '7 days'
GROUP BY b.batch_id, b.batch_number, p.product_name, b.production_date, b.expiry_date, b.current_quantity
ORDER BY b.expiry_date ASC, b.batch_id ASC;

-- 4. Оптимальная последовательность отгрузки (FEFO)
SELECT 
    r.reservation_id,
    o.order_number,
    c.client_name,
    p.product_name,
    b.batch_number,
    b.expiry_date,
    b.warehouse_location,
    r.reserved_quantity,
    o.delivery_date,
    EXTRACT(DAY FROM b.expiry_date - CURRENT_DATE) as days_to_expiry,
    CASE 
        WHEN b.expiry_date <= CURRENT_DATE THEN 'ПРОСРОЧЕНА'
        WHEN b.expiry_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'КРИТИЧНАЯ'
        WHEN b.expiry_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'СРОЧНАЯ'
        ELSE 'НОРМАЛЬНАЯ'
    END as urgency_level
FROM reservations r
JOIN order_items oi ON r.order_item_id = oi.order_item_id
JOIN orders o ON oi.order_id = o.order_id
JOIN batches b ON r.batch_id = b.batch_id
JOIN products p ON b.product_id = p.product_id
JOIN clients c ON o.client_id = c.client_id
WHERE r.reservation_status = 'active' 
    AND o.order_status IN ('confirmed', 'in_production', 'ready')
ORDER BY b.expiry_date ASC, o.delivery_date ASC, r.reservation_priority ASC;
