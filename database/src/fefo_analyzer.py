import pandas as pd
from tabulate import tabulate
from db_connection import DatabaseConnection

class FefoAnalyzer:
    """Класс для анализа данных и формирования отчетов по FEFO-оптимизации"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.db.connect()

    def get_clients_sales(self):
        """Возвращает общий объем заказов по клиентам"""
        query = """
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
        """
        result = self.db.execute_query(query)
        if result:
            df = pd.DataFrame(result)
            return df
        return pd.DataFrame()

    def get_stock_analysis(self):
        """Возвращает анализ остатков продукции по складам"""
        query = """
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
        """
        result = self.db.execute_query(query)
        if result:
            df = pd.DataFrame(result)
            return df
        return pd.DataFrame()

    def get_fefo_shipping_sequence(self):
        """Возвращает оптимальную последовательность отгрузки (FEFO)"""
        query = """
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
        """
        result = self.db.execute_query(query)
        if result:
            df = pd.DataFrame(result)
            return df
        return pd.DataFrame()

    def print_report(self, df, title):
        """Выводит DataFrame в виде красивой таблицы"""
        if df.empty:
            print(f"\n--- {title} ---")
            print("Нет данных для отображения.")
            return
            
        print(f"\n{'='*80}")
        print(f"{title.center(80)}")
        print(f"{'='*80}")
        
        # Заменяем NaN на '0' или пустую строку для красивого вывода
        df = df.fillna('')
        
        # Выводим таблицу с использованием tabulate
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        print("\n")

    def close(self):
        self.db.close()

if __name__ == "__main__":
    print("Инициализация анализатора FEFO...")
    analyzer = FefoAnalyzer()
    
    try:
        # Получаем и выводим отчеты
        clients_df = analyzer.get_clients_sales()
        analyzer.print_report(clients_df, "Объем заказов по клиентам")
        
        stock_df = analyzer.get_stock_analysis()
        analyzer.print_report(stock_df, "Анализ остатков продукции")
        
        fefo_df = analyzer.get_fefo_shipping_sequence()
        analyzer.print_report(fefo_df, "Оптимальная последовательность отгрузки (FEFO)")
        
    except Exception as e:
        print(f"Произошла ошибка при выполнении запросов: {e}")
        print("Убедитесь, что база данных инициализирована скриптом sql/01_init_db.sql")
    finally:
        analyzer.close()
