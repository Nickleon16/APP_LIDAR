# init_db.py

from db_connection import SessionLocal
from modelos import Usuario, Parametro, Base
import datetime

# create_schema.py
from db_connection import engine

# Crear las tablas en la base de datos
Base.metadata.create_all(engine)

def crear_usuario_admin():
    session = SessionLocal()
    try:
        admin = session.query(Usuario).filter_by(username='admin').first()
        if admin:
            print("El usuario 'admin' ya existe.")
        else:
            nuevo_admin = Usuario(
                nombre='Administrador del sistema',
                email='admin@example.com',
                username='admin',
                password='admin',
                rol='Administrador',
                user_status='Activo'
            )
            session.add(nuevo_admin)
            session.commit()
            print("Usuario administrador creado exitosamente.")
    except Exception as e:
        print(f"[ERROR] al crear el admin: {e}")
        session.rollback()
    finally:
        session.close()

def crear_parametros_por_defecto():
    session = SessionLocal()
    try:
        existe = session.query(Parametro).filter(Parametro.usuario_id == None).first()
        if existe:
            print("Los parámetros por defecto ya existen.")
        else:
            parametros = Parametro(
                usuario_id=None,
                nombre_preset="Default",
                descripcion="Parámetros por defecto",
                velocidad_maxima=2.0,
                velocidad_lineal=1.0,
                velocidad_angular=1.0,
                tasa_muestreo=10,
                campo_vision=180.0,
                #resolucion="Alta",
                #filtro_ruido="Media",
                #metodo_filtrado="Filtro Gaussiano",
                #reduccion_ruido="Media",
                #compensacion_movimiento="Compensación básica",
                #metodo_procesamiento="ICP",
                #tolerancia=0.01,
                #iteraciones=50,
                #correspondencia="KD-Tree",
                fecha=datetime.datetime.utcnow()
            )
            session.add(parametros)
            session.commit()
            print("Parámetros por defecto creados exitosamente.")
    except Exception as e:
        print(f"[ERROR] al crear parámetros por defecto: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    crear_usuario_admin()
    crear_parametros_por_defecto()
