from flask import Flask, render_template,redirect, request, session, url_for, flash
import pymysql.cursors
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
from pymysql.err import IntegrityError
import os
import pymysql
from datetime import datetime
import uuid
import time
from functools import wraps
import sys
sys.stderr = open('error.log', 'w')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/img'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('usuario_id') or session.get('rol') != 'admin':
            flash("Debes iniciar sesión como administrador.")
            return redirect(url_for('login_admin'))
        return f(*args, **kwargs)
    return decorated_function

def solicitante_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('usuario_id') or session.get('rol') != 'solicitante':
            flash("Debes iniciar sesión como solicitante.")
            return redirect(url_for('login_solicitante'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

@app.route('/')
def inicio():
    return render_template("inicio.html")

#@app.route('/inicio')
#def inicio_():
#    return render_template("inicio.html")


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


def obtener_todos_los_usuarios():
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, apellido, correo, rol, activo FROM usuarios WHERE rol = 'admin'")
            usuarios = cursor.fetchall()  
    finally:
        conexion.close()
    return usuarios


@app.route("/crear_solicitud", methods=["GET", "POST"])
def crear_solicitud():
    # 1. Verificar sesión y usuario válido
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión como solicitante.")
        return redirect(url_for("login_solicitante"))

    usuario_id = session.get('usuario_id')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE id=%s", (usuario_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("El usuario actual no existe. Inicia sesión de nuevo.")
        return redirect(url_for("login_solicitante"))

    if request.method == "POST":
        # DATOS PRINCIPALES
        tipo = request.form.get('tipo')
        observaciones = request.form.get('observaciones')
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        vcpu = to_int(request.form.get('vcpu', ''))
        ram = to_int(request.form.get('ram', ''))
        disco_sistema = to_int(request.form.get('disco_sistema', ''))
        disco_datos = to_int(request.form.get('disco_datos', ''))

        # INSERTAR EN solicitudes
        cursor.execute("""
            INSERT INTO solicitudes (usuario_id, tipo, fecha_solicitud, estado, observaciones)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario_id, tipo, fecha, "pendiente", observaciones))
        solicitud_id = cursor.lastrowid

        # DATOS DETALLADOS
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

        # INSERTAR EN solicitud_detalle
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

        # GUARDAR ARCHIVOS ADJUNTOS
        archivos = request.files.getlist('documentos')
        for archivo in archivos:
            if archivo and allowed_file(archivo.filename):
                ext = archivo.filename.rsplit('.', 1)[-1].lower()
                nombre_unico = f"{solicitud_id}_{int(time.time())}_{uuid.uuid4().hex}.{ext}"
                nombre_unico = secure_filename(nombre_unico)
                ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
                archivo.save(ruta)
                cursor.execute("""
                    INSERT INTO documentos_adjuntos (solicitud_id, nombre_archivo, ruta_archivo)
                    VALUES (%s, %s, %s)
                """, (solicitud_id, archivo.filename, nombre_unico))

        conn.commit()
        conn.close()
        flash("¡Solicitud enviada correctamente!")
        return redirect(url_for("solicitud_enviada"))

    conn.close()
    return render_template("formulario_crear.html")


@app.route("/solicitud_enviada")
def solicitud_enviada():
    return render_template("enviado.html")


# Conexión a base de datos
#def get_connection():
#    return pymysql.connect(
#        host='172.22.12.212',
#        user='flask_user',
#        password='S3rv!d0r2025',
#        database='sistema_solicitudes',
#        port=3306,
#        cursorclass=pymysql.cursors.DictCursor

#    )

def get_connection():
    return pymysql.connect(
        host='localhost',  # ← CAMBIA ESTO
        user='root',       # o tu usuario local
        password='2636587',
        database='sistema_solicitudes',
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


def obtener_logo():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = 'logo_municipio'")
    result = cursor.fetchone()
    conn.close()
    
    return result.get('valor', 'img/logo_municipio3.png') if result else 'img/logo_municipio3.png'
    
@app.context_processor
def inject_logo():
    return dict(logo_path=obtener_logo())



@app.route('/usuarios')
def usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return '<br>'.join([f"{u[1]} ({u[4]})" for u in usuarios])


@app.route('/login_admin', methods=['GET'])
def login_admin():
    return render_template('login_admin.html')


@app.route('/verificar_login_admin', methods=['POST'])
def verificar_login_admin():
    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM usuarios WHERE correo=%s AND password=%s AND rol='admin'", (usuario, password))
    admin = cursor.fetchone()
    conn.close()

    
    if not admin:
        flash('Credenciales incorrectas o no es administrador.')
        return redirect(url_for('login_admin'))

    
    if 'activo' in admin and admin['activo'] == 0:
        flash('Usuario deshabilitado. Contacta al administrador principal.')
        return redirect(url_for('login_admin'))

    session['usuario_id'] = admin['id']
    session['rol'] = admin['rol']
    return redirect(url_for('dashboard_admin'))


@app.route('/dashboard_admin')
@admin_required
def dashboard_admin():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT s.id, s.tipo, s.fecha_solicitud, s.estado, 
            CONCAT(u.nombre, ' ', u.apellido) AS nombre_admin_revisor
        FROM solicitudes s
        LEFT JOIN usuarios u ON s.id_admin_revisor = u.id
        ORDER BY s.fecha_solicitud DESC
    """)

    solicitudes = cursor.fetchall()
    conn.close()

    logo_path = obtener_logo()
    return render_template('dashboard_admin.html', solicitudes=solicitudes, logo_path=logo_path)


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

        # Buscar si el usuario ya existe por correo
        cursor.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
        usuario = cursor.fetchone()

        if not usuario:
            try:
                cursor.execute("""
                    INSERT INTO usuarios (nombre, apellido, correo, rol, password)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, apellido, correo, 'solicitante', None))
                conn.commit()
            except IntegrityError:
                # Si falla por duplicado, vuelve a buscar
                conn.rollback()
            cursor.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
            usuario = cursor.fetchone()

        conn.close()

        if usuario:
            session['usuario_id'] = usuario['id']
            session['nombre'] = nombre
            return redirect(url_for('dashboard_solicitante'))
        else:
            flash("No se pudo iniciar sesión, contacte al administrador.")
            return render_template('login_solicitante.html')

    return render_template('login_solicitante.html')

@app.route('/dashboard_solicitante')
def dashboard_solicitante():
    if 'usuario_id' not in session:
        return redirect(url_for('login_solicitante'))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, apellido FROM usuarios WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        nombre = usuario['nombre'] or ""
        apellido = usuario['apellido'] or ""
    else:
        nombre = ""
        apellido = ""

    nombre_completo = f"{nombre} {apellido}".strip()
    return render_template('dashboard_solicitante.html', nombre=nombre_completo)


@app.route('/historial_solicitante')
def historial():
    usuario_id = session['usuario_id'] 
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT s.id, s.tipo, s.fecha_solicitud, s.estado, s.observaciones, u.nombre AS nombre_admin_revisor
        FROM solicitudes s
        LEFT JOIN usuarios u ON s.id_admin_revisor = u.id
        WHERE s.usuario_id = %s
        ORDER BY s.fecha_solicitud DESC
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
        id_admin = session.get('usuario_id')
        print('ID del admin revisor:', id_admin)
        if accion == 'aprobar':
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE solicitudes SET estado='aprobado', id_admin_revisor=%s WHERE id=%s",
                        (id_admin, id)
                    )
                    conn.commit()
            return redirect(url_for('dashboard_admin'))
        elif accion == 'rechazar':
            observacion = request.form['observacion']
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE solicitudes SET estado='rechazado', observaciones=%s, id_admin_revisor=%s WHERE id=%s",
                        (observacion, id_admin, id)
                    )
                    conn.commit()
            return redirect(url_for('dashboard_admin'))

    
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
        observaciones_adicionales = request.form.get('observaciones_adicionales', '')
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

@app.route('/actualizar_logo', methods=['GET', 'POST'])
@admin_required
def actualizar_logo():
    if request.method == 'POST':
        file = request.files['logo']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"logo_municipio.{ext}"  # Siempre el mismo nombre si quieres sobrescribir
            file.save(os.path.join('static/img', filename))
            # Actualizar la ruta en la base de datos:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE configuracion SET valor = %s WHERE clave = 'logo_municipio'
            """, (f"img/{filename}",))
            conn.commit()
            conn.close()
            flash('Logo actualizado correctamente.')
            return redirect(url_for('dashboard_admin'))
    return render_template('actualizar_logo.html')

@app.route('/agregar_usuario', methods=['GET', 'POST'])
@admin_required
def agregar_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        rol = request.form['rol']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
     
        if password != password_confirm:
            return render_template('agregar_usuario.html', error="Las contraseñas no coinciden.")

     
        if len(password) < 4:
            return render_template('agregar_usuario.html', error="La contraseña debe tener al menos 4 caracteres.")
       
        admin_id = session.get('usuario_id')
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE id=%s AND rol='admin'", (admin_id,))
        admin = cursor.fetchone()
        cursor.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
        usuario = cursor.fetchone()
        if usuario:
            conn.close()
            return render_template('agregar_usuario.html', error="El correo ya está registrado.")

        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, correo, rol, password)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre, apellido, correo, rol, password))
        conn.commit()
        conn.close()
        return render_template('agregar_usuario.html', exito="Usuario agregado correctamente.")

    return render_template('agregar_usuario.html')

@app.context_processor
def inject_logo():
    return dict(logo_path=obtener_logo())

@app.route('/ver_usuarios')
@admin_required
def ver_usuarios():

    usuarios = obtener_todos_los_usuarios() 
    return render_template('ver_usuarios.html', usuarios=usuarios)

#@app.route('/eliminar_usuario/<int:id>')
#def eliminar_usuario(id):
#
#    if 'usuario_id' not in session:
#        return redirect(url_for('login_admin'))
#    
#    if id == session['usuario_id']:
#        flash("No puedes eliminarte a ti mismo.")
#        return redirect(url_for('ver_usuarios'))
#
#    conn = get_connection()
#    cursor = conn.cursor()
#    cursor.execute("DELETE FROM usuarios WHERE id=%s AND rol='admin'", (id,))
#    conn.commit()
#    conn.close()
#    flash('Administrador eliminado correctamente.')
#    return redirect(url_for('ver_usuarios'))


@app.route('/crear_recurso_compartido', methods=['GET', 'POST'])
def crear_recurso_compartido():
    if 'usuario_id' not in session:
        return redirect(url_for('login_solicitante'))

    if request.method == 'POST':
        usuario_id = session['usuario_id']
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Recoger campos del formulario
        nombre_solicitante = request.form['nombre_completo']
        dependencia = request.form['unidad']
        cargo = request.form['cargo']
        correo = request.form['correo']
        telefono = request.form['telefono']
        nombre_recurso = request.form['nombre_recurso']
        ubicacion = request.form['ubicacion']
        proposito = request.form['proposito']
        usuarios_acceso = request.form['usuarios_acceso']
        permisos = request.form['permisos']
        tipo_info = request.form['tipo_info']
        volumen = request.form['volumen']
        tiempo_uso = request.form['tiempo_uso']
        firma_solicitante = request.form['firma_solicitante']
        firma_jefe = request.form['firma_jefe']
        cargo_solicitante = request.form['cargo_solicitante']
        cargo_jefe = request.form['cargo_jefe']

        conn = get_connection()
        cursor = conn.cursor()

        # Insertar solicitud
        cursor.execute("""
            INSERT INTO solicitudes (usuario_id, tipo, fecha_solicitud, estado)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, 'recursos', fecha, 'pendiente'))
        solicitud_id = cursor.lastrowid

        # Insertar detalle
        cursor.execute("""
            INSERT INTO solicitud_detalle (
                solicitud_id, fecha, nombre_completo, unidad, cargo, correo, telefono,
                nombre_recurso, ubicacion, proposito, usuarios_acceso, permisos,
                tipo_informacion, volumen, tiempo_uso,
                firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            solicitud_id, fecha, nombre_solicitante, dependencia, cargo, correo, telefono,
            nombre_recurso, ubicacion, proposito, usuarios_acceso, permisos,
            tipo_info, volumen, tiempo_uso,
            firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
        ))

        conn.commit()
        conn.close()
        flash("¡Solicitud de recurso compartido enviada correctamente!")
        return redirect(url_for("solicitud_enviada"))

    return render_template('formulario_recursos.html')

@app.route('/editar_recurso_compartido/<int:id>', methods=['GET', 'POST'])
@solicitante_required
def editar_recurso_compartido(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener datos existentes
    cursor.execute("SELECT * FROM recursos_compartidos WHERE id = %s", (id,))
    detalle = cursor.fetchone()

    # Verificar si existe observación del administrador
    cursor.execute("SELECT observacion FROM observaciones WHERE recurso_id = %s", (id,))
    obs_result = cursor.fetchone()
    observacion = obs_result['observacion'] if obs_result else None

    if request.method == 'POST':
        data = {
            'nombre_completo': request.form['nombre_completo'],
            'unidad': request.form['unidad'],
            'correo': request.form['correo'],
            'telefono': request.form['telefono'],
            'nombre_carpeta': request.form['nombre_carpeta'],
            'justificacion': request.form['justificacion'],
            'unidad_creacion': request.form['unidad_creacion'],
            'usuarios_acceso': request.form['usuarios_acceso'],
            'responsable': request.form['responsable'],
            'correo_responsable': request.form['correo_responsable'],
            'observaciones': request.form['observaciones'],
            'firma_solicitante': request.form['firma_solicitante'],
            'cargo_solicitante': request.form['cargo_solicitante'],
            'firma_jefe': request.form['firma_jefe'],
            'cargo_jefe': request.form['cargo_jefe'],
        }

        sql = """
        UPDATE recursos_compartidos SET
            nombre_completo = %(nombre_completo)s,
            unidad = %(unidad)s,
            correo = %(correo)s,
            telefono = %(telefono)s,
            nombre_carpeta = %(nombre_carpeta)s,
            justificacion = %(justificacion)s,
            unidad_creacion = %(unidad_creacion)s,
            usuarios_acceso = %(usuarios_acceso)s,
            responsable = %(responsable)s,
            correo_responsable = %(correo_responsable)s,
            observaciones = %(observaciones)s,
            firma_solicitante = %(firma_solicitante)s,
            cargo_solicitante = %(cargo_solicitante)s,
            firma_jefe = %(firma_jefe)s,
            cargo_jefe = %(cargo_jefe)s
        WHERE id = %s
        """
        cursor.execute(sql, (*data.values(), id))
        conn.commit()
        conn.close()
        flash('Solicitud actualizada correctamente.', 'success')
        return redirect(url_for('dashboard_solicitante'))

    conn.close()
    return render_template("editar_recurso_compartido.html", detalle=detalle, observacion=observacion)


@app.route('/revisar_recurso_compartido/<int:id>', methods=['GET', 'POST'])
@solicitante_required
def revisar_recurso_compartido(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM recursos_compartidos WHERE id = %s", (id,))
    detalle = cursor.fetchone()

    if request.method == 'POST':
        if request.form['accion'] == 'aprobar':
            cursor.execute("UPDATE recursos_compartidos SET estado = 'Aprobado' WHERE id = %s", (id,))
            conn.commit()
            flash("Solicitud aprobada.", "success")
        elif request.form['accion'] == 'rechazar':
            observacion = request.form['observacion']
            cursor.execute("UPDATE recursos_compartidos SET estado = 'Rechazado' WHERE id = %s", (id,))
            cursor.execute("INSERT INTO observaciones (recurso_id, observacion) VALUES (%s, %s)", (id, observacion))
            conn.commit()
            flash("Solicitud rechazada con observación.", "danger")
        conn.close()
        return redirect(url_for('dashboard_admin'))

    conn.close()
    return render_template("revisar_recurso_compartido.html", detalle=detalle)


@app.route('/cambiar_estado_usuario/<int:id>/<int:nuevo_estado>')
@admin_required
def cambiar_estado_usuario(id, nuevo_estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, id))
    conn.commit()
    conn.close()
    return redirect(url_for('ver_usuarios'))


# Iniciar servidor
#if __name__ == '__main__':
#   app.run(debug=True, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)


application = app


