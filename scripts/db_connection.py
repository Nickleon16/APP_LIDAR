import mysql.connector

def get_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='qwer',  
            database='APP_LIDAR_db'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"[ERROR] No se pudo conectar a la base de datos: {err}")
        return None
