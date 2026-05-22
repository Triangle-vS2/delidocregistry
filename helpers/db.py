import pymysql

def get_db():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='Mysql_1',
        database='None',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )