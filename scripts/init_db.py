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
            # Telemetria
                velocidad_lineal = 2,
                velocidad_angular = 2,

                # Captura de nubes
                num_steps = 60,
                max_range = 10,
                min_range = 0,
                fov_angel = 45,
                prefijo = "nube",
                # preprocesamiento
                vecinos = 5,
                dev_std = 2,
                z_max = 10,
                z_min = 0,
                voxel_size = 0.15,

                # procesamiento
                num_planos = 5,
                distancia = 0.01,
                iteraciones = 100,

                # alineacion
                voxel_size_ali = 0.15,
                normal_rad = 0.30,
                normal_max_nn = 45,
                fpfh_rad = 5,
                fpfh_max_nn = 100,    
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
