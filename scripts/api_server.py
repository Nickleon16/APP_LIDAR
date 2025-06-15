# api_server.py

import io
from flask import Flask, request, jsonify, send_file
import mysql.connector  
from db_connection import get_connection

app = Flask(__name__)

#-------------------------------------------------------------------------------
# /api/login: "POST"/login
#-------------------------------------------------------------------------------

@app.route('/api/login', methods=['POST'])
def login():
    conn = None
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        conn = get_connection()
        if conn is None:
            raise Exception("Conexión fallida")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM usuarios 
            WHERE username = %s AND password = %s
        """, (username, password))

        user = cursor.fetchone()
        if user:
            return jsonify({
                'status': 'success',
                'message': 'Login exitoso',
                'userID': user[0],  
                'username': username
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Credenciales inválidas'}), 401

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------
# /api/usuarios: "POST"/crear_usuario - "GET"/obtener_usuarios 
#                "PUT"/update_usuario - "DELETE"/eliminar_usuario
#-------------------------------------------------------------------------------

@app.route("/api/usuarios", methods=["POST"])
def crear_usuario():
    data = request.get_json()
    nombre = data.get("nombre")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    rol = data.get("rol")
    status = data.get("status")

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, username, password, rol, user_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, email, username, password, rol, status))
        conn.commit()
        return jsonify({"message": "Usuario creado"}), 201

    except mysql.connector.IntegrityError:
        return jsonify({"error": "El usuario ya existe"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    conn = None
    try:        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT userID, nombre, email, username, rol, user_status 
            FROM usuarios
        """)
        usuarios = cursor.fetchall()        
        return jsonify({"usuarios": usuarios}), 200
    except Exception as e:        
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
def update_usuario(user_id):
    data = request.get_json()

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios 
            SET nombre = %s, email = %s, username = %s, password = %s, rol = %s, user_status = %s 
            WHERE userID = %s
        """, (
            data["nombre"],
            data["email"],
            data["username"],
            data["password"],
            data["rol"],
            data["status"],
            user_id
        ))

        conn.commit()
        affected_rows = cursor.rowcount

        if affected_rows == 0:
            return jsonify({"error": "Usuario no encontrado o sin cambios"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
def eliminar_usuario(user_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE userID = %s", (user_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------
# /api/parametros: "GET"/obtener_parametros - "POST"/crear_parametro
#                "PUT"/actualizar_parametro - "DELETE"/eliminar_parametro
#-------------------------------------------------------------------------------

@app.route('/api/parametros/por_usuario/<int:usuario_id>', methods=['GET'])
def obtener_parametros_por_usuario(usuario_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT parametroID, nombre_preset, descripcion, fecha
            FROM parametros
            WHERE usuario_id = %s
            ORDER BY fecha DESC
        """, (usuario_id,))
        parametros = cursor.fetchall()
        
        return jsonify({"parametros": parametros}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/<int:parametro_id>', methods=['GET'])
def obtener_parametros_por_id(parametro_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM parametros WHERE parametroID = %s", (parametro_id,))
        parametro = cursor.fetchone()

        if parametro:
            return jsonify({"parametros": parametro}), 200
        else:
            return jsonify({"error": "No se encontró el preset"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/default', methods=['GET'])
def obtener_parametros_default():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM parametros 
            WHERE usuario_id IS NULL 
            ORDER BY fecha DESC 
            LIMIT 1
        """)
        parametros = cursor.fetchone()

        if parametros:
            return jsonify({"parametros": parametros}), 200
        else:
            return jsonify({"error": "No existen parámetros por defecto."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros', methods=['POST'])
def crear_parametro():
    data = request.get_json()
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO parametros (
            usuario_id, nombre_preset, descripcion,
            velocidad_maxima, velocidad_lineal, velocidad_angular,
            tasa_muestreo, campo_vision, resolucion, filtro_ruido,
            metodo_filtrado, reduccion_ruido, compensacion_movimiento,
            metodo_procesamiento, tolerancia, iteraciones, correspondencia
        ) VALUES (%s, %s, %s, 
                    %s, %s, %s,
                    %s, %s, %s, %s, 
                    %s, %s, %s, 
                    %s, %s, %s, %s)

        """, (
            data["usuario_id"], data["nombre_preset"], data["descripcion"], data["velocidad_maxima"],
            data["velocidad_lineal"], data["velocidad_angular"], data["tasa_muestreo"],
            data["campo_vision"], data["resolucion"], data["filtro_ruido"],
            data["metodo_filtrado"], data["reduccion_ruido"], data["compensacion_movimiento"],
            data["metodo_procesamiento"], data["tolerancia"], data["iteraciones"],
            data["correspondencia"]
        ))

        conn.commit()
        return jsonify({"message": "Preset creado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/<int:parametro_id>', methods=['PUT'])
def actualizar_parametro(parametro_id):
    data = request.get_json()
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE parametros SET
                nombre_preset = %s, descripcion = %s,
                velocidad_maxima = %s, velocidad_lineal = %s, velocidad_angular = %s,
                tasa_muestreo = %s, campo_vision = %s, resolucion = %s, filtro_ruido = %s,
                metodo_filtrado = %s, reduccion_ruido = %s, compensacion_movimiento = %s,
                metodo_procesamiento = %s, tolerancia = %s, iteraciones = %s, correspondencia = %s
            WHERE parametroID = %s
        """, (
            data["nombre_preset"], data["descripcion"], data["velocidad_maxima"],
            data["velocidad_lineal"], data["velocidad_angular"], data["tasa_muestreo"],
            data["campo_vision"], data["resolucion"], data["filtro_ruido"],
            data["metodo_filtrado"], data["reduccion_ruido"], data["compensacion_movimiento"],
            data["metodo_procesamiento"], data["tolerancia"], data["iteraciones"],
            data["correspondencia"], parametro_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "No se encontró el preset"}), 404
        return jsonify({"message": "Preset actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/parametros/<int:parametro_id>', methods=['DELETE'])
def eliminar_parametro(parametro_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM parametros WHERE parametroID = %s", (parametro_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "No se encontró el preset"}), 404
        return jsonify({"message": "Preset eliminado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

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
    print(f"Tamaño recibido: {len(datos)} bytes")  # DEBUG

    tipo = archivo.filename.split('.')[-1]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO nubes_de_puntos (nombre, descripcion, archivo_tipo, nube_datos, nombre_archivo)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, descripcion, tipo, datos, nombre_archivo))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Nube guardada"}), 201

#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos', methods=['GET'])
def listar_nubes():
    try:        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nubeID, nombre, descripcion, archivo_tipo, fecha FROM nubes_de_puntos ORDER BY fecha DESC")
        nubes = cursor.fetchall()        
        return jsonify({"nubes": nubes}), 200
    except Exception as e:        
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

#-------------------------------------------------------------------------------

@app.route('/api/nube_puntos/<int:id>', methods=['GET'])
def descargar_nube(id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nube_datos, nombre, archivo_tipo FROM nubes_de_puntos WHERE nubeID = %s", (id,))
        nube = cursor.fetchone()
        cursor.close()
        conn.close()

        if not nube:
            return jsonify({"error": "Nube no encontrada"}), 404

        extension = nube['archivo_tipo']
        nombre_archivo = f"{nube['nombre']}.{extension}"

        return send_file(
            io.BytesIO(nube["nube_datos"]),
            mimetype='application/octet-stream',
            download_name=nombre_archivo,
            as_attachment=False
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)