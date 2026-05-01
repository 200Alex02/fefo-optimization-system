import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

class DatabaseConnection:
    """Класс для управления подключением к базе данных PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.dbname = os.getenv("DB_NAME", "fefo_optimization_db")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")
        self.conn = None

    def connect(self):
        """Устанавливает подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            return self.conn
        except psycopg2.Error as e:
            print(f"Ошибка при подключении к базе данных: {e}")
            return None

    def close(self):
        """Закрывает подключение к базе данных"""
        if self.conn is not None:
            self.conn.close()
            print("Подключение к базе данных закрыто.")

    def execute_query(self, query, params=None, fetch=True):
        """Выполняет SQL-запрос"""
        if self.conn is None:
            self.connect()
            
        if self.conn is None:
            return None
            
        try:
            # Используем RealDictCursor для получения результатов в виде словарей
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    return cursor.fetchall()
                else:
                    self.conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            self.conn.rollback()
            return None

# Пример использования:
if __name__ == "__main__":
    db = DatabaseConnection()
    conn = db.connect()
    
    if conn:
        print(f"Успешно подключено к базе данных {db.dbname}")
        
        # Простой тестовый запрос
        try:
            result = db.execute_query("SELECT current_database(), current_user, version();")
            if result:
                print("\nИнформация о базе данных:")
                for key, value in result[0].items():
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"Не удалось выполнить тестовый запрос. Возможно база данных еще не инициализирована. Ошибка: {e}")
            
        db.close()
    else:
        print("Не удалось подключиться. Проверьте настройки в файле .env")
