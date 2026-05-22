import pymysql

def test_db_connection():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='password',
            database='users_db'
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False