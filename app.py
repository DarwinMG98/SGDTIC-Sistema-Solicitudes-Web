from flask import Flask, render_template,redirect, request, session, url_for, flash
import pymysql.cursors
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
import os
import pymysql
from datetime import datetime
import uuid
import time

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

def to_int(valor):
    """Convierte valor a int si no está vacío, si no, retorna None"""
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/crear_solicitud", methods=["GET", "POST"])
def crear_solicitud():
    if request.method == "POST":
        tipo = request.form.get('tipo')
        observaciones = request.form.get('observaciones')
        usuario_id = session.get('usuario_id')
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        vcpu = to_int(request.form.get('vcpu', ''))
        ram = to_int(request.form.get('ram', ''))
        disco_sistema = to_int(request.form.get('disco_sistema', ''))
        disco_datos = to_int(request.form.get('disco_datos', ''))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO solicitudes (usuario_id, tipo, fecha_solicitud, estado, observaciones)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario_id, tipo, fecha, "pendiente", observaciones))
        solicitud_id = cursor.lastrowid

        nombre_completo = request.form['nombre_completo']
        unidad = request.form['unidad']
        correo = request.form['correo']
        telefono = request.form['telefono']
        responsable_tecnico = request.form['responsable_tecnico']
        origen_solicitud = ', '.join(request.form.getlist('origen[]'))
        anteproyecto = request.form['anteproyecto']
        motivo = request.form['motivo']
        tipo_servidor = ', '.join(request.form.getlist('tipo_servidor[]'))
        sistema_operativo = request.form['sistema_operativo']
        version_so = (
            request.form.get('version_windows', '') or
            request.form.get('version_linux', '') or
            request.form.get('so_otro', '')
        )
        vida_util = request.form['vida_util']
        justificacion_recursos = request.form['justificacion_recursos']
        accesos = request.form['accesos']
        responsable_aplicacion = request.form['responsable_aplicacion']
        unidad_responsable = request.form['unidad_responsable']
        contacto_soporte = request.form['contacto_soporte']
        observaciones_adicionales = request.form['observaciones']  
        firma_solicitante = request.form['firma_solicitante']
        cargo_solicitante = request.form['cargo_solicitante']
        firma_jefe = request.form['firma_jefe']
        cargo_jefe = request.form['cargo_jefe']

        cursor.execute("""
            INSERT INTO solicitud_detalle (
                solicitud_id, fecha, nombre_completo, unidad, correo, telefono, responsable_tecnico,
                origen_solicitud, anteproyecto, motivo, tipo_servidor, sistema_operativo, version_so,
                vcpu, ram, disco_sistema, disco_datos, vida_util, justificacion_recursos, accesos,
                responsable_aplicacion, unidad_responsable, contacto_soporte, observaciones_adicionales,
                firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            solicitud_id, fecha, nombre_completo, unidad, correo, telefono, responsable_tecnico,
            origen_solicitud, anteproyecto, motivo, tipo_servidor, sistema_operativo, version_so,
            vcpu, ram, disco_sistema, disco_datos, vida_util, justificacion_recursos, accesos,
            responsable_aplicacion, unidad_responsable, contacto_soporte, observaciones_adicionales,
            firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
        ))

              # ======= GUARDAR ARCHIVOS ADJUNTOS =======
        archivos = request.files.getlist('documentos')

        print("FILES RECIBIDOS:", request.files)
        print("archivos:", archivos)
        for archivo in archivos:
            print("archivo:", archivo.filename)

        for archivo in archivos:
            if archivo and allowed_file(archivo.filename):
                ext = archivo.filename.rsplit('.', 1)[-1].lower()
                nombre_unico = f"{solicitud_id}_{int(time.time())}_{uuid.uuid4().hex}.{ext}"
                nombre_unico = secure_filename(nombre_unico)
                ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
                archivo.save(ruta)  # Guarda en /uploads/nombre_unico.pdf

                # Registrar en la tabla documentos_adjuntos
                cursor.execute("""
                    INSERT INTO documentos_adjuntos (solicitud_id, nombre_archivo, ruta_archivo)
                    VALUES (%s, %s, %s)
                """, (solicitud_id, archivo.filename, nombre_unico))  # Guardas el nombre original, y el nombre físico real

        conn.commit()
        conn.close()
        return redirect(url_for("solicitud_enviada"))

    return render_template("formulario_crear.html")


@app.route("/solicitud_enviada")
def solicitud_enviada():
    return render_template("enviado.html")


# Conexión a base de datos
def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='2636587',
        database='sistema_solicitudes'

    )

def obtener_logo():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = 'logo_municipio'")
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 'img/logo_municipio3.png'
    
@app.context_processor
def inject_logo():
    return dict(logo_path=obtener_logo())

# Página de inicio
@app.route('/')
def inicio():
    return render_template("inicio.html")


@app.route('/usuarios')
def usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return '<br>'.join([f"{u[1]} ({u[4]})" for u in usuarios])


@app.route('/login_admin')
def login_admin():
    return render_template('login_admin.html')


@app.route('/verificar_login_admin', methods=['POST'])
def verificar_login_admin():
    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE correo=%s AND contraseña=%s AND rol='admin'", (usuario, password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        return redirect('/dashboard_admin')
    else:
        return "Credenciales incorrectas o no es administrador"


@app.route('/dashboard_admin')
def dashboard_admin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, fecha_solicitud, estado FROM solicitudes ORDER BY fecha_solicitud DESC")
    solicitudes = cursor.fetchall()
    conn.close()
    print("SOLICITUDES DASHBOARD ADMIN", solicitudes)
    return render_template('dashboard_admin.html', solicitudes=solicitudes)


@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('inicio'))

@app.route('/login_solicitante', methods=['GET', 'POST'])
def login_solicitante():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']

        conn = get_connection()
        cursor = conn.cursor()

        
        cursor.execute("SELECT * FROM solicitantes WHERE nombre=%s AND apellido=%s AND correo=%s", 
                       (nombre, apellido, correo))
        solicitante = cursor.fetchone()

        
        if not solicitante:
            cursor.execute("INSERT INTO solicitantes (nombre, apellido, correo) VALUES (%s, %s, %s)", 
                           (nombre, apellido, correo))
            conn.commit()
            cursor.execute("SELECT * FROM solicitantes WHERE nombre=%s AND apellido=%s AND correo=%s", 
                           (nombre, apellido, correo))
            solicitante = cursor.fetchone()

        conn.close()

        
        if solicitante:
            session['usuario_id'] = solicitante[0]
            session['nombre'] = solicitante[1]
            return redirect(url_for('dashboard_solicitante'))
        else:
            return "No se pudo iniciar sesión"
    return render_template('login_solicitante.html')

@app.route('/dashboard_solicitante')
def dashboard_solicitante():
    if 'usuario_id' not in session:
        return redirect(url_for('login_solicitante'))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, apellido FROM solicitantes WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()
    conn.close()

   
    nombre = usuario[0] if usuario[0] else ""
    apellido = usuario[1] if usuario[1] else ""

    nombre_completo = f"{nombre} {apellido}".strip()

    return render_template('dashboard_solicitante.html', nombre=nombre_completo)

@app.route('/historial_solicitante')
def historial():
    usuario_id = session['usuario_id'] 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tipo, fecha_solicitud, estado, observaciones
        FROM solicitudes
        WHERE usuario_id = %s
        ORDER BY fecha_solicitud DESC
    """, (usuario_id,))
    solicitudes = cursor.fetchall()
    conn.close()
    return render_template('historial_solicitante.html', solicitudes=solicitudes)
    

@app.route("/enviado")
def enviado():
    return render_template("enviado.html")


@app.route('/revisar_solicitud/<int:id>', methods=['GET', 'POST'])
def revisar_solicitud(id):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
    solicitud = cursor.fetchone()

    cursor.execute("SELECT * FROM solicitud_detalle WHERE solicitud_id=%s", (id,))
    detalle = cursor.fetchone()
    cursor.execute("SELECT * FROM documentos_adjuntos WHERE solicitud_id = %s", (id,))
    documentos = cursor.fetchall()
    
    conn.close()

    if request.method == 'POST':
        accion = request.form['accion']
        if accion == 'aprobar':
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id=%s", (id,))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard_admin'))
        elif accion == 'rechazar':
            observacion = request.form['observacion']
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE solicitudes SET estado='rechazado', observaciones=%s WHERE id=%s", (observacion, id))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard_admin'))

    # == CAMBIO AQUÍ ==
    if solicitud['tipo'] == 'eliminar':
        return render_template(
            'revisar_solicitud_eliminar.html',
            solicitud=solicitud,
            detalle=detalle,
            documentos=documentos
        )
    else:
        return render_template(
            'revisar_solicitud.html',
            solicitud=solicitud,
            detalle=detalle,
            documentos=documentos
        )

@app.route('/editar_solicitud/<int:id>', methods=['GET', 'POST'])
def editar_solicitud(id):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
    solicitud = cursor.fetchone()
    cursor.execute("SELECT * FROM solicitud_detalle WHERE solicitud_id=%s", (id,))
    detalle = cursor.fetchone()
    cursor.execute("SELECT * FROM documentos_adjuntos WHERE solicitud_id=%s", (id,))
    documentos = cursor.fetchall()

    if request.method == "POST":
        
        nombre_completo = request.form.get('nombre_completo', '')
        unidad = request.form.get('unidad', '')
        correo = request.form.get('correo', '')
        telefono = request.form.get('telefono', '')
        responsable_tecnico = request.form.get('responsable_tecnico', '')
        origen_solicitud = ', '.join(request.form.getlist('origen[]'))
        anteproyecto = request.form.get('anteproyecto', '')
        motivo = request.form.get('motivo', '')
        tipo_servidor = ', '.join(request.form.getlist('tipo_servidor[]'))
        sistema_operativo = request.form.get('sistema_operativo', '')
        version_so = (
            request.form.get('version_windows', '') or
            request.form.get('version_linux', '') or
            request.form.get('so_otro', '')
        )
        vida_util = request.form.get('vida_util', '')
        justificacion_recursos = request.form.get('justificacion_recursos', '')
        accesos = request.form.get('accesos', '')
        responsable_aplicacion = request.form.get('responsable_aplicacion', '')
        unidad_responsable = request.form.get('unidad_responsable', '')
        contacto_soporte = request.form.get('contacto_soporte', '')
        observaciones_adicionales = request.form.get('observaciones', '')
        firma_solicitante = request.form.get('firma_solicitante', '')
        cargo_solicitante = request.form.get('cargo_solicitante', '')
        firma_jefe = request.form.get('firma_jefe', '')
        cargo_jefe = request.form.get('cargo_jefe', '')
        vcpu = to_int(request.form.get('vcpu', ''))
        ram = to_int(request.form.get('ram', ''))
        disco_sistema = to_int(request.form.get('disco_sistema', ''))
        disco_datos = to_int(request.form.get('disco_datos', ''))

        vcpu = to_int(request.form.get('vcpu', ''))
        ram = to_int(request.form.get('ram', ''))
        disco_sistema = to_int(request.form.get('disco_sistema', ''))
        disco_datos = to_int(request.form.get('disco_datos', ''))


        cursor.execute("""
            UPDATE solicitud_detalle SET
                nombre_completo=%s, unidad=%s, correo=%s, telefono=%s, responsable_tecnico=%s,
                origen_solicitud=%s, anteproyecto=%s, motivo=%s, tipo_servidor=%s, sistema_operativo=%s, version_so=%s,
                vcpu=%s, ram=%s, disco_sistema=%s, disco_datos=%s, vida_util=%s, justificacion_recursos=%s,
                accesos=%s, responsable_aplicacion=%s, unidad_responsable=%s, contacto_soporte=%s, observaciones_adicionales=%s,
                firma_solicitante=%s, cargo_solicitante=%s, firma_jefe=%s, cargo_jefe=%s
            WHERE solicitud_id=%s
        """, (
            nombre_completo, unidad, correo, telefono, responsable_tecnico, origen_solicitud, anteproyecto, motivo,
            tipo_servidor, sistema_operativo, version_so, vcpu, ram, disco_sistema, disco_datos, vida_util, justificacion_recursos,
            accesos, responsable_aplicacion, unidad_responsable, contacto_soporte, observaciones_adicionales,
            firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe, id
        ))

        cursor.execute("UPDATE solicitudes SET estado='pendiente' WHERE id=%s", (id,))

                # ===== GUARDAR ARCHIVOS ADJUNTOS NUEVOS =====
        archivos = request.files.getlist('documentos')
        for archivo in archivos:
            if archivo and archivo.filename and allowed_file(archivo.filename):
                filename = secure_filename(archivo.filename)
                ruta = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                archivo.save(ruta)
                cursor.execute("""
                    INSERT INTO documentos_adjuntos (solicitud_id, nombre_archivo, ruta_archivo)
                    VALUES (%s, %s, %s)
                """, (id, filename, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("historial"))


    conn.close()

    if solicitud['tipo'] == 'crear':
        return render_template("formulario_editar.html", detalle=detalle, documentos=documentos, observacion=solicitud['observaciones'])
    elif solicitud['tipo'] == 'eliminar':
        return render_template("formulario_editar_eliminar.html", detalle=detalle, documentos=documentos, observacion=solicitud['observaciones'])


@app.route('/uploads/<filename>')
def descargar_archivo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/crear_eliminacion', methods=['GET', 'POST'])
def crear_eliminacion():
    if request.method == "POST":
        tipo = "eliminar"
        usuario_id = session.get('usuario_id')
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # ----- Paso 1 -----
        nombre_completo = request.form['nombre_completo']
        unidad = request.form['unidad']
        correo = request.form['correo']
        telefono = request.form['telefono']
        responsable_tecnico = request.form.get('responsable_tecnico', '')

        # ----- Paso 2 -----
        nombre_servidor = request.form.get('nombre_servidor', '')
        ip_servidor = request.form.get('ip_servidor', '')
        sistema_operativo = request.form.get('sistema_operativo', '')
        rol_servidor = ', '.join(request.form.getlist('rol_servidor[]'))
        fecha_creacion_servidor = request.form.get('fecha_creacion_servidor', '')
        motivo_eliminacion = request.form.get('motivo_eliminacion', '')

        # ----- Paso 3 -----
        validaciones = ', '.join(request.form.getlist('validaciones[]'))

        # ----- Paso 4 -----
        motivo_check = ', '.join(request.form.getlist('motivo_check[]'))
        motivo_otro = request.form.get('motivo_otro', '')

        # ----- Paso 5 -----
        observaciones_adicionales = request.form.get('observaciones_adicionales', '')

        # ----- Paso 6 -----
        firma_solicitante = request.form.get('firma_solicitante', '')
        cargo_solicitante = request.form.get('cargo_solicitante', '')
        firma_jefe = request.form.get('firma_jefe', '')
        cargo_jefe = request.form.get('cargo_jefe', '')

        conn = get_connection()
        cursor = conn.cursor()

        
        cursor.execute("""
            INSERT INTO solicitudes (usuario_id, tipo, fecha_solicitud, estado)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, tipo, fecha, "pendiente"))
        solicitud_id = cursor.lastrowid

        
        cursor.execute("""
            INSERT INTO solicitud_detalle (
                solicitud_id, fecha, nombre_completo, unidad, correo, telefono, responsable_tecnico,
                nombre_servidor, ip_servidor, sistema_operativo, rol_servidor, fecha_creacion_servidor,
                motivo_eliminacion, validaciones, motivo_check, motivo_otro,
                observaciones_adicionales, firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            solicitud_id, fecha, nombre_completo, unidad, correo, telefono, responsable_tecnico,
            nombre_servidor, ip_servidor, sistema_operativo, rol_servidor, fecha_creacion_servidor,
            motivo_eliminacion, validaciones, motivo_check, motivo_otro,
            observaciones_adicionales, firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
        ))

        
        archivos = request.files.getlist('documentos')
        for archivo in archivos:
            if archivo and archivo.filename and allowed_file(archivo.filename):
                filename = secure_filename(archivo.filename)
                ruta = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                archivo.save(ruta)
                cursor.execute("""
                    INSERT INTO documentos_adjuntos (solicitud_id, nombre_archivo, ruta_archivo)
                    VALUES (%s, %s, %s)
                """, (solicitud_id, filename, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("solicitud_enviada"))

    return render_template("formulario_eliminar.html")


# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)

