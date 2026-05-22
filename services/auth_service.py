import pymysql

def authenticate_user(username: str, password: str) -> bool:
    # Connect to the database
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='Pymysql_1',
            database='None'
        )

        with conn.cursor() as cursor:
            # Query to check if the user exists with the provided username and password
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password)
                        )
            user = cursor.fetchone()

        conn.close()
        return user is not None
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return False