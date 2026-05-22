import pymysql, configparser, logging
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        self.connection = None
    
    @contextmanager
    def get_cursor(self):
        cursor = None
        try:
            if not self.connection or not self.connection.is_connected():
                self._connect()
            cursor = self.connection.cursor(prepared=True)
            yield cursor
            self.connection.commit()
        except Error as e:
            if cursor:
                cursor.close()
            logger.error(f"Database error: {e}")
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
    
    def _connect(self):
        config = configparser.ConfigParser()
        if not config.read('contacts.cfg'):
            raise RuntimeError("contacts.cfg not found")
        
        if 'database' not in config:
            raise RuntimeError("No [database] section in contacts.cfg")
        
        delidocdb_config = config['database']
        self.connection = pymysql.connect(
            host=delidocdb_config['host'],
            user=delidocdb_config['user'],
            password=delidocdb_config['pass'],
            database=delidocdb_config['db'],
            autocommit=False
        )
        logger.info("✓ Database connected")
    
    def execute_query(self, query: str, params=None) -> List[tuple]:
        """Execute query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
db_manager = DatabaseManager()


class DelidocDB:
    def __init__(self, host='localhost', user='root', password='Mysql_1', database=None):
        self.conn = pymysql.connect(host=host, user=user, password=password,
                                    database=database, cursorclass=DictCursor, autocommit=False)
        self.cursor = self.conn.cursor()

    def create_database_and_table(self, delidoc_name='delidocdb'):
        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{delidoc_name}`;")
        self.cursor.execute(f"USE `{delidoc_name}`;")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            account VARCHAR(255) NOT NULL,
            item VARCHAR(255) NOT NULL,
            quantity INT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS items (
            id VARCHAR(64) PRIMARY KEY,
            sku VARCHAR(64),
            name VARCHAR(255),
            count INT DEFAULT 1,
            zone VARCHAR(32),
            category VARCHAR(64)
            value_code VARCHAR(16)
        );
        
        """)
        self.conn.commit()

    def create_order(self, customer, item, quantity):
        sql = "INSERT INTO orders (customer, item, quantity) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (customer, item, quantity))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_orders(self):
        self.cursor.execute("SELECT * FROM orders")
        return self.cursor.fetchall()

    def update_order(self, order_id, new_quantity):
        sql = "UPDATE orders SET quantity = %s WHERE id = %s"
        self.cursor.execute(sql, (new_quantity, order_id))
        self.conn.commit()
        return self.cursor.rowcount

    def delete_order(self, order_id):
        sql = "DELETE FROM orders WHERE id = %s"
        self.cursor.execute(sql, (order_id,))
        self.conn.commit()
        return self.cursor.rowcount

    def close(self):
        try:
            self.cursor.close()
        finally:
            self.conn.close()


def sql_flow():
    db = DelidocDB()
    try:
        db.create_database_and_table()

        # create
        id1 = db.create_order("Alice", "Widget", 5)
        id2 = db.create_order("Bob", "Gadget", 3)

        # read
        print("Current Users:")
        for order in db.get_orders():
            print(order)

        # update
        db.update_order(order_id=id1, new_quantity=10)

        # delete
        db.delete_order(order_id=id2)

        print("Final Users:")
        for order in db.get_orders():
            print(order)
    finally:
        db.close()

if __name__ == "__main__":
    sql_flow()