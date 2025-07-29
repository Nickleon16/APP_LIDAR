# api_server.py

from sqlalchemy.orm import Session
from db_connection import SessionLocal
from modelos import Usuario, Parametro, NubeDePuntos
import io
from flask import Flask, request, jsonify, send_file
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

#-------------------------------------------------------------------------------
# /api/login: "POST"/login
#-------------------------------------------------------------------------------

@app.route('/api/login', methods=['POST'])
def login():
    db: Session = SessionLocal()
    try:
        data = request.json
        user = db.query(Usuario).filter_by(username=data['username'], password=data['password']).first()

        if user:
            return jsonify({
                'status': 'success',
                'message': 'Login exitoso',
                'userID': user.userID,
                'username': user.username
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Credenciales inválidas'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------
# /api/usuarios: "POST"/crear_usuario - "GET"/obtener_usuarios 
#                "PUT"/update_usuario - "DELETE"/eliminar_usuario
#-------------------------------------------------------------------------------

@app.route("/api/usuarios", methods=["POST"])
def crear_usuario():
    db: Session = SessionLocal()
    try:
        data = request.get_json()

        nuevo_usuario = Usuario(
            nombre=data["nombre"],
            email=data["email"],
            username=data["username"],
            password=data["password"],
            rol=data["rol"],
            user_status=data["status"]
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        return jsonify({"message": "Usuario creado", "userID": nuevo_usuario.userID}), 201

    except IntegrityError as e:
        db.rollback()
        if 'username' in str(e.orig).lower():
            return jsonify({"error": "El nombre de usuario ya está en uso"}), 400
        return jsonify({"error": "El nombre de usuario ya está en uso"}), 500

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    db: Session = SessionLocal()
    try:
        usuarios = db.query(Usuario).all()
        resultado = [
            {
                "userID": u.userID,
                "nombre": u.nombre,
                "email": u.email,
                "username": u.username,
                "rol": u.rol,
                "status": u.user_status
            } for u in usuarios
        ]
        return jsonify({"usuarios": resultado}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
def update_usuario(user_id):
    db: Session = SessionLocal()
    try:
        data = request.get_json()
        usuario = db.query(Usuario).filter_by(userID=user_id).first()

        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        for field in ["nombre", "email", "username", "password", "rol", "status"]:
            setattr(usuario, field if field != "status" else "user_status", data[field])

        db.commit()
        return jsonify({"message": "Usuario actualizado"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
def eliminar_usuario(user_id):
    db: Session = SessionLocal()
    try:
        usuario = db.query(Usuario).filter_by(userID=user_id).first()

        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        db.delete(usuario)
        db.commit()
        return jsonify({"message": "Usuario eliminado"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------
# /api/parametros: "GET"/obtener_parametros - "POST"/crear_parametro
#                "PUT"/actualizar_parametro - "DELETE"/eliminar_parametro
#-------------------------------------------------------------------------------

@app.route('/api/parametros/por_usuario/<int:usuario_id>', methods=['GET'])
def obtener_parametros_por_usuario(usuario_id):
    db: Session = SessionLocal()
    try:
        parametros = db.query(Parametro)\
            .filter(Parametro.usuario_id == usuario_id)\
            .order_by(Parametro.fecha.desc())\
            .all()

        resultado = [
            {
                "parametroID": p.parametroID,
                "nombre_preset": p.nombre_preset,
                "descripcion": p.descripcion,
                "fecha": p.fecha.isoformat()
            } for p in parametros
        ]
        return jsonify({"parametros": resultado}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/<int:parametro_id>', methods=['GET'])
def obtener_parametros_por_id(parametro_id):
    db: Session = SessionLocal()
    try:
        parametro = db.get(Parametro, parametro_id)  # <- esto cambia
        if parametro:
            resultado = {
                "parametroID": parametro.parametroID,
                "nombre_preset": parametro.nombre_preset,
                "descripcion": parametro.descripcion,
                "fecha": parametro.fecha.isoformat() if parametro.fecha else None,
                "velocidad_maxima": parametro.velocidad_maxima,
                "velocidad_lineal": parametro.velocidad_lineal,
                "velocidad_angular": parametro.velocidad_angular,
                "tasa_muestreo": parametro.tasa_muestreo,
                "campo_vision": parametro.campo_vision,
                "resolucion": parametro.resolucion
                # TODO: Agregar los campos restantes
                #"filtro_ruido": parametro.filtro_ruido,
                #"metodo_filtrado": parametro.metodo_filtrado,
                #"reduccion_ruido": parametro.reduccion_ruido,
                #"compensacion_movimiento": parametro.compensacion_movimiento,
                #"metodo_procesamiento": parametro.metodo_procesamiento,
                #"tolerancia": parametro.tolerancia,
                #"iteraciones": parametro.iteraciones,
                #"correspondencia": parametro.correspondencia
            }
            return jsonify({"parametros": resultado}), 200
        return jsonify({"error": "No se encontró el preset"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/default', methods=['GET'])
def obtener_parametros_default():
    db: Session = SessionLocal()
    try:
        parametro = db.query(Parametro)\
            .filter(Parametro.usuario_id == None)\
            .order_by(Parametro.fecha.desc())\
            .first()

        if parametro:
            resultado = {
                "parametroID": parametro.parametroID,
                "nombre_preset": parametro.nombre_preset,
                "descripcion": parametro.descripcion,
                "fecha": parametro.fecha.isoformat() if parametro.fecha else None,
                "velocidad_maxima": parametro.velocidad_maxima,
                "velocidad_lineal": parametro.velocidad_lineal,
                "velocidad_angular": parametro.velocidad_angular,
                "tasa_muestreo": parametro.tasa_muestreo,
                "campo_vision": parametro.campo_vision,
                "resolucion": parametro.resolucion,
                "filtro_ruido": parametro.filtro_ruido,
                "metodo_filtrado": parametro.metodo_filtrado,
                "reduccion_ruido": parametro.reduccion_ruido,
                "compensacion_movimiento": parametro.compensacion_movimiento,
                "metodo_procesamiento": parametro.metodo_procesamiento,
                "tolerancia": parametro.tolerancia,
                "iteraciones": parametro.iteraciones,
                "correspondencia": parametro.correspondencia
            }
            return jsonify({"parametros": resultado}), 200

        return jsonify({"error": "No existen parámetros por defecto."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros', methods=['POST'])
def crear_parametro():
    data = request.get_json()
    db: Session = SessionLocal()
    try:
        parametro = Parametro(**data)
        db.add(parametro)
        db.commit()
        db.refresh(parametro)
        return jsonify({"message": "Preset creado", "parametroID": parametro.parametroID}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/<int:parametro_id>', methods=['PUT'])
def actualizar_parametro(parametro_id):
    data = request.get_json()
    db: Session = SessionLocal()
    try:
        parametro = db.query(Parametro).get(parametro_id)
        if not parametro:
            return jsonify({"error": "No se encontró el preset"}), 404

        for key, value in data.items():
            setattr(parametro, key, value)

        db.commit()
        return jsonify({"message": "Preset actualizado"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/<int:parametro_id>', methods=['DELETE'])
def eliminar_parametro(parametro_id):
    db: Session = SessionLocal()
    try:
        parametro = db.query(Parametro).get(parametro_id)
        if not parametro:
            return jsonify({"error": "No se encontró el preset"}), 404

        db.delete(parametro)
        db.commit()
        return jsonify({"message": "Preset eliminado"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------
# /api/nube_puntos: "GET"/obtener_nube - "POST"/crear_nube
#                "PUT"/actualizar_nube - "DELETE"/eliminar_nube
#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos', methods=['POST'])
def subir_nube_puntos():
    archivo = request.files['archivo']
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    nombre_archivo = request.form.get('nombre_archivo')

    if not archivo:
        return jsonify({"error": "No se envió archivo"}), 400

    datos = archivo.read()
    tipo = archivo.filename.split('.')[-1]

    db: Session = SessionLocal()
    try:
        nube = NubeDePuntos(
            nombre=nombre,
            descripcion=descripcion,
            archivo_tipo=tipo,
            nombre_archivo=nombre_archivo,
            nube_datos=datos
        )
        db.add(nube)
        db.commit()
        return jsonify({"mensaje": "Nube guardada"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos', methods=['GET'])
def listar_nubes():
    db: Session = SessionLocal()
    try:
        nubes = db.query(NubeDePuntos).order_by(NubeDePuntos.fecha.desc()).all()
        resultado = [
            {
                "nubeID": n.nubeID,
                "nombre": n.nombre,
                "descripcion": n.descripcion,
                "archivo_tipo": n.archivo_tipo,
                "nombre_archivo": n.nombre_archivo,
                "fecha": n.fecha.isoformat()
            } for n in nubes
        ]
        return jsonify({"nubes": resultado}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos/<int:id>', methods=['GET'])
def descargar_nube(id):
    db: Session = SessionLocal()
    try:
        nube = db.get(NubeDePuntos, id)
        if not nube:
            return jsonify({"error": "Nube no encontrada"}), 404

        extension = nube.archivo_tipo
        nombre_archivo = f"{nube.nombre}.{extension}"

        return send_file(
            io.BytesIO(nube.nube_datos),
            mimetype='application/octet-stream',
            download_name=nombre_archivo,
            as_attachment=False
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos/<int:id>/info', methods=['GET'])
def obtener_info_nube(id):
    db: Session = SessionLocal()
    try:
        nube = db.get(NubeDePuntos, id)
        if not nube:
            return jsonify({"error": "Nube no encontrada"}), 404

        return jsonify({
            "nubeID": nube.nubeID,
            "nombre": nube.nombre,
            "descripcion": nube.descripcion,
            "archivo_tipo": nube.archivo_tipo,
            "nombre_archivo": nube.nombre_archivo,
            "fecha": nube.fecha.isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos/<int:id>', methods=['DELETE'])
def eliminar_nube(id):
    db: Session = SessionLocal()
    try:
        nube = db.query(NubeDePuntos).get(id)
        if not nube:
            return jsonify({"error": "Nube no encontrada"}), 404

        db.delete(nube)
        db.commit()
        return jsonify({"mensaje": "Nube eliminada"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)