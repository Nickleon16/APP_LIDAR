# init_db.py

from db_connection import get_connection
import mysql.connector

def crear_usuario_admin():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si ya existe un admin
        cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone():
            print("El usuario 'admin' ya existe.")
        else:
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, username, password, rol, user_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                'Administrador del sistema',
                'admin@example.com',
                'a',
                'a',
                'Administrador',
                'Activo'
            ))
            conn.commit()
            print("Usuario administrador creado exitosamente.")

    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")

    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

def crear_parametros_por_defecto():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si ya existen parámetros globales
        cursor.execute("""
            SELECT * FROM parametros WHERE usuario_id IS NULL
        """)
        if cursor.fetchone():
            print("Los parámetros por defecto ya existen.")
        else:
            cursor.execute("""
                INSERT INTO parametros (
                    usuario_id, descripcion, nombre_preset,
                    velocidad_maxima, velocidad_lineal, velocidad_angular,
                    tasa_muestreo, campo_vision, resolucion, filtro_ruido,
                    metodo_filtrado, reduccion_ruido, compensacion_movimiento,
                    metodo_procesamiento, tolerancia, iteraciones, correspondencia
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                None, "Parámetros por defecto", "Default",
                2.0, 1.0, 0.5,               # velocidades
                10, 180.0, "Alta", "Media",   # captura
                "Filtro Gaussiano", "Media", "Compensación básica", # preprocesamiento
                "ICP", 0.01, 50, "KD-Tree"    # procesamiento
            ))
            conn.commit()
            print("Parámetros por defecto creados exitosamente.")

    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    crear_usuario_admin()
    crear_parametros_por_defecto()
