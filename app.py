from flask import Flask, render_template,redirect, request, session, url_for, flash, send_file, make_response
import pymysql.cursors
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
from pymysql.err import IntegrityError
from weasyprint import HTML
import os
import pymysql
from datetime import datetime
import uuid
import time
from functools import wraps
import sys
import re
sys.stderr = open('error.log', 'w')



app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

PDF_FOLDER = os.path.join(app.root_path, 'storage', 'pdfs')
os.makedirs(PDF_FOLDER, exist_ok=True)

def guardar_pdf(html, solicitud_id):
    nombre = f"solicitud_{solicitud_id}.pdf"
    ruta = os.path.join(PDF_FOLDER, nombre)
    HTML(string=html, base_url=app.root_path).write_pdf(ruta)
    return nombre

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

def parse_vida_util(texto: str) -> int | None:
    """
    Convierte '2 meses', '1 año 6 meses', '18 meses', '3' (meses) -> meses (int)
    """
    if not texto: return None
    t = texto.lower().strip()
    anos = 0; meses = 0
    m = re.search(r'(\d+)\s*a(ño|nos)', t)
    if m: anos = int(m.group(1))
    m = re.search(r'(\d+)\s*mes', t)
    if m: meses = int(m.group(1))
    if anos == 0 and meses == 0 and t.isdigit():
        meses = int(t)
    total = anos*12 + meses
    return total if total > 0 else None


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
        vida_util_meses = parse_vida_util(vida_util) 
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

                # ========= PEGAR AQUÍ (NUEVO) =========
        # Guarda los meses derivados en el detalle
        cursor.execute("""
            UPDATE solicitud_detalle
            SET vida_util_meses=%s
            WHERE solicitud_id=%s
        """, (vida_util_meses, solicitud_id))

        # Expiración provisional (desde fecha_solicitud ya guardada)
        if vida_util_meses:
            cursor.execute("""
                UPDATE solicitudes
                SET fecha_expiracion = DATE_ADD(DATE(fecha_solicitud), INTERVAL %s MONTH)
                WHERE id=%s
            """, (vida_util_meses, solicitud_id))
        else:
            cursor.execute("UPDATE solicitudes SET fecha_expiracion=NULL WHERE id=%s", (solicitud_id,))
        # ========= HASTA AQUÍ =========

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
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute("""
        SELECT COUNT(*) c
        FROM solicitudes
        WHERE fecha_expiracion IS NOT NULL
          AND DATEDIFF(fecha_expiracion, CURDATE()) BETWEEN 1 AND 7
    """)
    por_vencer_count = cur.fetchone()['c']

    cur.execute("""
        SELECT COUNT(*) c
        FROM solicitudes
        WHERE fecha_expiracion IS NOT NULL
          AND DATEDIFF(fecha_expiracion, CURDATE()) <= 0
    """)
    vencidos_count = cur.fetchone()['c']

    cur.execute("""
        SELECT s.id,
               s.tipo,
               s.fecha_solicitud,
               s.estado,
               DATE_FORMAT(s.fecha_expiracion,'%Y-%m-%d') AS fecha_expiracion,
               DATEDIFF(s.fecha_expiracion, CURDATE()) AS dias_restantes,
               CASE
                 WHEN s.fecha_expiracion IS NULL THEN 'sin_fecha'
                 WHEN DATEDIFF(s.fecha_expiracion, CURDATE()) <= 0 THEN 'vencido'
                 WHEN DATEDIFF(s.fecha_expiracion, CURDATE()) <= 7 THEN 'por_vencer'
                 ELSE 'ok'
               END AS estado_exp,
               COALESCE(CONCAT(u.nombre,' ',u.apellido), '---') AS nombre_admin_revisor
        FROM solicitudes s
        LEFT JOIN usuarios u ON s.id_admin_revisor = u.id
        ORDER BY s.fecha_solicitud DESC
    """)
    solicitudes = cur.fetchall()
    conn.close()

    return render_template('dashboard_admin.html',
                           solicitudes=solicitudes,
                           por_vencer_count=por_vencer_count,
                           vencidos_count=vencidos_count)


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
@admin_required
def revisar_solicitud(id):
    with get_connection() as conn:
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
        solicitud = cur.fetchone()
        cur.execute("SELECT * FROM solicitud_detalle WHERE solicitud_id=%s", (id,))
        detalle = cur.fetchone() or {}
        cur.execute("SELECT * FROM documentos_adjuntos WHERE solicitud_id=%s", (id,))
        documentos = cur.fetchall()

    if not solicitud:
        flash("Solicitud no encontrada.")
        return redirect(url_for('dashboard_admin'))

    if request.method == 'POST':
        accion = request.form.get('accion')
        id_admin = session.get('usuario_id')

        with get_connection() as conn:
            # usaremos cursores dict para leer y normal para actualizar
            cur = conn.cursor()
            cur_det = conn.cursor(pymysql.cursors.DictCursor)

            if accion == 'aprobar':
                # 1) leer meses desde el detalle
                cur_det.execute(
                    "SELECT vida_util_meses FROM solicitud_detalle WHERE solicitud_id=%s",
                    (id,)
                )
                det = cur_det.fetchone()
                meses = det['vida_util_meses'] if det and det['vida_util_meses'] else None

                # 2) actualizar cabecera con fecha_aprobacion y expiracion
                if meses:
                    cur.execute("""
                        UPDATE solicitudes
                        SET estado='aprobado',
                            id_admin_revisor=%s,
                            fecha_aprobacion=NOW(),
                            fecha_expiracion=DATE_ADD(CURDATE(), INTERVAL %s MONTH)
                        WHERE id=%s
                    """, (id_admin, meses, id))
                else:
                    cur.execute("""
                        UPDATE solicitudes
                        SET estado='aprobado',
                            id_admin_revisor=%s,
                            fecha_aprobacion=NOW(),
                            fecha_expiracion=NULL
                        WHERE id=%s
                    """, (id_admin, id))

            elif accion == 'rechazar':
                observacion = request.form.get('observacion','')
                cur.execute("""
                    UPDATE solicitudes
                    SET estado='rechazado',
                        observaciones=%s,
                        id_admin_revisor=%s
                    WHERE id=%s
                """, (observacion, id_admin, id))

            conn.commit()

        return redirect(url_for('dashboard_admin'))

    # GET -> plantilla por tipo
    if solicitud.get('tipo') == 'recursos':
        return render_template('revisar_recurso_compartido.html',
                               solicitud=solicitud, detalle=detalle)
    elif solicitud.get('tipo') == 'eliminar':
        return render_template('revisar_solicitud_eliminar.html',
                               solicitud=solicitud, detalle=detalle, documentos=documentos)
    else:  # crear
        return render_template('revisar_solicitud.html',
                               solicitud=solicitud, detalle=detalle, documentos=documentos)



@app.route('/revisar_recurso_compartido/<int:solicitud_id>')
def revisar_recurso_compartido_legacy(solicitud_id):
    return redirect(url_for('revisar_solicitud', id=solicitud_id))


@app.route('/editar_solicitud/<int:id>', methods=['GET', 'POST'])
def editar_solicitud(id):
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # Cargar cabecera + detalle + docs
    cur.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
    solicitud = cur.fetchone()
    cur.execute("SELECT * FROM solicitud_detalle WHERE solicitud_id=%s", (id,))
    detalle = cur.fetchone() or {}
    cur.execute("SELECT * FROM documentos_adjuntos WHERE solicitud_id=%s", (id,))
    documentos = cur.fetchall()

    if not solicitud:
        conn.close()
        flash("Solicitud no encontrada.", "warning")
        return redirect(url_for('historial'))

    if request.method == 'POST':
        tipo = solicitud.get('tipo')

        # ---------- EDITAR RECURSOS COMPARTIDOS ----------
        if tipo == 'recursos':
            nombre_completo   = request.form.get('nombre_completo','').strip()
            unidad            = request.form.get('unidad','').strip()
            cargo             = request.form.get('cargo','').strip()
            correo            = request.form.get('correo','').strip()
            telefono          = request.form.get('telefono','').strip()
            nombre_recurso    = request.form.get('nombre_recurso','').strip()
            ubicacion         = request.form.get('ubicacion','').strip()
            proposito         = request.form.get('proposito','').strip()
            usuarios_acceso   = request.form.get('usuarios_acceso','').strip()
            permisos          = request.form.get('permisos','').strip()
            tipo_informacion  = request.form.get('tipo_informacion','').strip()
            volumen           = request.form.get('volumen','').strip()
            tiempo_uso        = request.form.get('tiempo_uso','').strip()
            firma_solicitante = request.form.get('firma_solicitante','').strip()
            cargo_solicitante = request.form.get('cargo_solicitante','').strip()
            firma_jefe        = request.form.get('firma_jefe','').strip()
            cargo_jefe        = request.form.get('cargo_jefe','').strip()

            cur.execute("""
                UPDATE solicitud_detalle SET
                    nombre_completo=%s, unidad=%s, cargo=%s, correo=%s, telefono=%s,
                    nombre_recurso=%s, ubicacion=%s, proposito=%s, usuarios_acceso=%s, permisos=%s,
                    tipo_informacion=%s, volumen=%s, tiempo_uso=%s,
                    firma_solicitante=%s, cargo_solicitante=%s, firma_jefe=%s, cargo_jefe=%s
                WHERE solicitud_id=%s
            """, (nombre_completo, unidad, cargo, correo, telefono,
                nombre_recurso, ubicacion, proposito, usuarios_acceso, permisos,
                tipo_informacion, volumen, tiempo_uso,
                firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe, id))

            # === vida útil -> meses y expiración ===
            vida_util_meses = parse_vida_util(tiempo_uso)
            cur.execute("UPDATE solicitud_detalle SET vida_util_meses=%s WHERE solicitud_id=%s",
                        (vida_util_meses, id))

            if vida_util_meses:
                cur.execute("""
                    UPDATE solicitudes
                    SET fecha_expiracion = DATE_ADD(DATE(fecha_solicitud), INTERVAL %s MONTH),
                        id_admin_revisor=NULL, estado='pendiente'
                    WHERE id=%s
                """, (vida_util_meses, id))
            else:
                cur.execute("""
                    UPDATE solicitudes
                    SET fecha_expiracion=NULL,
                        id_admin_revisor=NULL, estado='pendiente'
                    WHERE id=%s
                """, (id,))

            conn.commit(); conn.close()
            flash("Solicitud actualizada. Quedó nuevamente en revisión.", "success")
            return redirect(url_for('historial'))


        # ---------- EDITAR CREACIÓN DE SERVIDOR ----------
        elif tipo == 'crear':
            fecha  = request.form.get('fecha') or None
            nombre_completo = request.form.get('nombre_completo','').strip()
            unidad = request.form.get('unidad','').strip()
            correo = request.form.get('correo','').strip()
            telefono = request.form.get('telefono','').strip()
            responsable_tecnico = request.form.get('responsable_tecnico','').strip()

            origen = ', '.join(request.form.getlist('origen[]'))
            anteproyecto = request.form.get('anteproyecto','').strip()
            motivo = request.form.get('motivo','').strip()

            tipo_servidor = ', '.join(request.form.getlist('tipo_servidor[]'))
            so = request.form.get('sistema_operativo','').strip()
            v_win = request.form.get('version_windows','').strip()
            v_lin = request.form.get('version_linux','').strip()
            v_otr = request.form.get('so_otro','').strip()
            if so == 'Windows Server': version_so = v_win
            elif so == 'Linux':        version_so = v_lin
            elif so == 'Otro':         version_so = v_otr
            else:                      version_so = ''

            vcpu = request.form.get('vcpu') or None
            ram  = request.form.get('ram') or None
            disco_sistema = request.form.get('disco_sistema') or None
            disco_datos   = request.form.get('disco_datos') or None
            vida_util = request.form.get('vida_util','').strip()
            justificacion_recursos = request.form.get('justificacion_recursos','').strip()

            accesos = request.form.get('accesos','').strip()
            responsable_aplicacion = request.form.get('responsable_aplicacion','').strip()
            unidad_responsable = request.form.get('unidad_responsable','').strip()
            contacto_soporte  = request.form.get('contacto_soporte','').strip()
            observaciones_adicionales = request.form.get('observaciones','').strip()

            firma_solicitante = request.form.get('firma_solicitante','').strip()
            cargo_solicitante = request.form.get('cargo_solicitante','').strip()
            firma_jefe = request.form.get('firma_jefe','').strip()
            cargo_jefe = request.form.get('cargo_jefe','').strip()

            cur.execute("""
                UPDATE solicitud_detalle SET
                    fecha=%s, nombre_completo=%s, unidad=%s, correo=%s, telefono=%s,
                    responsable_tecnico=%s, origen_solicitud=%s, anteproyecto=%s, motivo=%s,
                    tipo_servidor=%s, sistema_operativo=%s, version_so=%s,
                    vcpu=%s, ram=%s, disco_sistema=%s, disco_datos=%s,
                    vida_util=%s, justificacion_recursos=%s,
                    accesos=%s, responsable_aplicacion=%s, unidad_responsable=%s,
                    contacto_soporte=%s, observaciones_adicionales=%s,
                    firma_solicitante=%s, cargo_solicitante=%s, firma_jefe=%s, cargo_jefe=%s
                WHERE solicitud_id=%s
            """, (fecha, nombre_completo, unidad, correo, telefono,
                responsable_tecnico, origen, anteproyecto, motivo,
                tipo_servidor, so, version_so,
                vcpu, ram, disco_sistema, disco_datos,
                vida_util, justificacion_recursos,
                accesos, responsable_aplicacion, unidad_responsable,
                contacto_soporte, observaciones_adicionales,
                firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe, id))

            # === vida útil -> meses y expiración (desde fecha_solicitud) ===
            vida_util_meses = parse_vida_util(vida_util)
            cur.execute("UPDATE solicitud_detalle SET vida_util_meses=%s WHERE solicitud_id=%s",
                        (vida_util_meses, id))

            if vida_util_meses:
                cur.execute("""
                    UPDATE solicitudes
                    SET fecha_expiracion = DATE_ADD(DATE(fecha_solicitud), INTERVAL %s MONTH),
                        id_admin_revisor=NULL, estado='pendiente'
                    WHERE id=%s
                """, (vida_util_meses, id))
            else:
                cur.execute("""
                    UPDATE solicitudes
                    SET fecha_expiracion=NULL,
                        id_admin_revisor=NULL, estado='pendiente'
                    WHERE id=%s
                """, (id,))

            conn.commit(); conn.close()
            flash('Solicitud actualizada. Quedó nuevamente en revisión.', 'success')
            return redirect(url_for('historial'))

        # ---------- EDITAR ELIMINACIÓN DE SERVIDOR ----------
        elif tipo == 'eliminar':
            # Paso 1
            nombre_completo = request.form.get('nombre_completo','').strip()
            unidad          = request.form.get('unidad','').strip()
            correo          = request.form.get('correo','').strip()
            telefono        = request.form.get('telefono','').strip()
            responsable_tecnico = request.form.get('responsable_tecnico','').strip()

            # Paso 2
            nombre_servidor = request.form.get('nombre_servidor','').strip()
            ip_servidor     = request.form.get('ip_servidor','').strip()
            sistema_operativo = request.form.get('sistema_operativo','').strip()
            rol_servidor    = ', '.join(request.form.getlist('rol_servidor[]'))
            fecha_creacion_servidor = request.form.get('fecha_creacion_servidor') or None
            motivo_eliminacion = request.form.get('motivo_eliminacion','').strip()

            # Paso 3
            validaciones    = ', '.join(request.form.getlist('validaciones[]'))

            # Paso 4
            motivo_check    = ', '.join(request.form.getlist('motivo_check[]'))
            motivo_otro     = request.form.get('motivo_otro','').strip()

            # Paso 5
            observaciones_adicionales = request.form.get('observaciones_adicionales','').strip()

            # Paso 6
            firma_solicitante = request.form.get('firma_solicitante','').strip()
            cargo_solicitante = request.form.get('cargo_solicitante','').strip()
            firma_jefe        = request.form.get('firma_jefe','').strip()
            cargo_jefe        = request.form.get('cargo_jefe','').strip()

            cur.execute("""
                UPDATE solicitud_detalle SET
                    nombre_completo=%s, unidad=%s, correo=%s, telefono=%s, responsable_tecnico=%s,
                    nombre_servidor=%s, ip_servidor=%s, sistema_operativo=%s, rol_servidor=%s,
                    fecha_creacion_servidor=%s, motivo_eliminacion=%s,
                    validaciones=%s, motivo_check=%s, motivo_otro=%s,
                    observaciones_adicionales=%s,
                    firma_solicitante=%s, cargo_solicitante=%s, firma_jefe=%s, cargo_jefe=%s
                WHERE solicitud_id=%s
            """, (nombre_completo, unidad, correo, telefono, responsable_tecnico,
                  nombre_servidor, ip_servidor, sistema_operativo, rol_servidor,
                  fecha_creacion_servidor, motivo_eliminacion,
                  validaciones, motivo_check, motivo_otro,
                  observaciones_adicionales,
                  firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe, id))

            cur.execute("UPDATE solicitudes SET estado='pendiente', id_admin_revisor=NULL WHERE id=%s", (id,))
            conn.commit(); conn.close()
            flash('Solicitud de eliminación actualizada. Quedó nuevamente en revisión.', 'success')
            return redirect(url_for('historial'))

        # Si el tipo no coincide
        else:
            conn.close()
            flash("Tipo de solicitud no reconocido.", "danger")
            return redirect(url_for('historial'))

    # ------- GET: render según tipo -------
    observacion_admin = solicitud.get('observaciones')  # o el nombre real de la columna

    if solicitud['tipo'] == 'recursos':
        conn.close()
        return render_template("formulario_editar_recursos.html",
                               solicitud=solicitud,
                               detalle=detalle, documentos=documentos,
                               observacion=observacion_admin)

    elif solicitud['tipo'] == 'crear':
        conn.close()
        return render_template("formulario_editar.html",
                               solicitud=solicitud,
                               detalle=detalle, documentos=documentos,
                               observacion=observacion_admin)

    elif solicitud['tipo'] == 'eliminar':
        conn.close()
        return render_template("formulario_editar_eliminar.html",
                               solicitud=solicitud,
                               detalle=detalle, documentos=documentos,
                               observacion=observacion_admin)



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
    if request.method == 'POST':
        f = request.form
        usuario_id = session.get('usuario_id')

        with get_connection() as conn:
            cur = conn.cursor()

            # 1) Cabecera: usa DEFAULTS (fecha_solicitud y estado='pendiente')
            cur.execute("""
                INSERT INTO solicitudes (usuario_id, tipo)
                VALUES (%s, %s)
            """, (usuario_id, 'recursos'))
            solicitud_id = cur.lastrowid

            # 2) Detalle: columnas y valores 1:1 (18 columnas, 18 %s)
            cur.execute("""
                INSERT INTO solicitud_detalle (
                    solicitud_id,
                    nombre_completo, unidad, cargo, correo, telefono,
                    nombre_recurso, ubicacion, proposito, usuarios_acceso, permisos,
                    tipo_informacion, volumen, tiempo_uso,
                    firma_solicitante, cargo_solicitante, firma_jefe, cargo_jefe
                )
                VALUES (
                    %s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,
                    %s,%s,%s,%s
                )
            """, (
                solicitud_id,
                f.get('nombre_completo'), f.get('unidad'), f.get('cargo'),
                f.get('correo'), f.get('telefono'),

                f.get('nombre_recurso'), f.get('ubicacion'), f.get('proposito'),
                f.get('usuarios_acceso'), f.get('permisos'),

                # En el form se llama "tipo_info", en BD la columna es "tipo_informacion"
                f.get('tipo_informacion'), f.get('volumen'), f.get('tiempo_uso'),

                f.get('firma_solicitante'), f.get('cargo_solicitante'),
                f.get('firma_jefe'), f.get('cargo_jefe')
            ))

            tiempo_uso = f.get('tiempo_uso') or ''
            meses = parse_vida_util(tiempo_uso)

            # guarda meses derivados
            cur.execute("""
                UPDATE solicitud_detalle
                SET vida_util_meses=%s
                WHERE solicitud_id=%s
            """, (meses, solicitud_id))

            # fija fecha de expiración provisional desde fecha_solicitud
            if meses:
                cur.execute("""
                    UPDATE solicitudes
                    SET fecha_expiracion = DATE_ADD(DATE(fecha_solicitud), INTERVAL %s MONTH)
                    WHERE id=%s
                """, (meses, solicitud_id))
            else:
                cur.execute("UPDATE solicitudes SET fecha_expiracion=NULL WHERE id=%s", (solicitud_id,))


            conn.commit()

        flash('Solicitud enviada con éxito.')
        return redirect(url_for('historial'))

    # GET
    return render_template('formulario_recursos.html', logo_path='img/logo_quito.png')


@app.route('/cambiar_estado_usuario/<int:id>/<int:nuevo_estado>')
@admin_required
def cambiar_estado_usuario(id, nuevo_estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, id))
    conn.commit()
    conn.close()
    return redirect(url_for('ver_usuarios'))


@app.route('/descargar_pdf/<int:id>')
def descargar_pdf(id):
    with get_connection() as conn:
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
        sol = cur.fetchone()
        if not sol:
            return "No existe la solicitud", 404

        cur.execute("SELECT * FROM solicitud_detalle WHERE solicitud_id=%s", (id,))
        det = cur.fetchone() or {}

        admin = None
        if sol.get('id_admin_revisor'):
            cur.execute("SELECT nombre, apellido FROM usuarios WHERE id=%s",(sol['id_admin_revisor'],))
            admin = cur.fetchone() or {}
            admin['cargo'] = 'Administrador de Infraestructura'

    html = generar_pdf_por_tipo(sol, det, admin)

    pdf_bytes = HTML(string=html, base_url=app.root_path).write_pdf()
    resp = make_response(pdf_bytes)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=solicitud_{id}.pdf'
    return resp


def plantilla_por_tipo(tipo):
    return {
        'crear':    'pdf_crear.html',        # tu plantilla actual de creación
        'eliminar': 'pdf/eliminacion.html',  # la que acabas de guardar
        'recurso':  'pdf/recurso.html',      # cuando la tengas lista
    }.get(tipo, 'pdf_crear.html')


# --- PDF de CREAR (tu plantilla pdf_crear.html) ---
def generar_pdf_solicitud(sol, det, admin=None):
    datos = {
        "fecha": (sol or {}).get("fecha_solicitud") or (det or {}).get("fecha"),
        "unidad": (det or {}).get("unidad"),
        "nombre_completo": (det or {}).get("nombre_completo"),
        "correo": (det or {}).get("correo"),
        "telefono": (det or {}).get("telefono"),
        "responsable_tecnico": (det or {}).get("responsable_tecnico"),
        "origen": (det or {}).get("origen_solicitud"),
        "anteproyecto": (det or {}).get("anteproyecto"),
        "motivo": (det or {}).get("motivo"),
        "tipo_servidor": (det or {}).get("tipo_servidor"),
        "sistema_operativo": (det or {}).get("sistema_operativo"),
        "version_windows": (det or {}).get("version_so"),
        "version_linux": (det or {}).get("version_so"),
        "so_otro": (det or {}).get("version_so"),
        "vcpu": (det or {}).get("vcpu"),
        "ram": (det or {}).get("ram"),
        "disco_sistema": (det or {}).get("disco_sistema"),
        "disco_datos": (det or {}).get("disco_datos"),
        "vida_util": (det or {}).get("vida_util"),
        "justificacion_recursos": (det or {}).get("justificacion_recursos"),
        "accesos": (det or {}).get("accesos"),
        "responsable_aplicacion": (det or {}).get("responsable_aplicacion"),
        "unidad_responsable": (det or {}).get("unidad_responsable"),
        "contacto_soporte": (det or {}).get("contacto_soporte"),
        "observaciones": (det or {}).get("observaciones_adicionales"),
        "firma_solicitante": (det or {}).get("firma_solicitante"),
        "cargo_solicitante": (det or {}).get("cargo_solicitante"),
        "firma_jefe": (det or {}).get("firma_jefe"),
        "cargo_jefe": (det or {}).get("cargo_jefe"),
        "nombre_servidor": (det or {}).get("nombre_servidor", ""),
    }

    aprobador = None
    if admin:
        aprobador = {
            "nombre": f"{admin.get('nombre','')} {admin.get('apellido','')}".strip(),
            "cargo": "Administrador de Infraestructura",
        }

    jefe_unidad = {
        "nombre": (det or {}).get("firma_jefe") or "",
        "cargo":  (det or {}).get("cargo_jefe") or "",
    }

    html = render_template(
        "pdf_crear.html",
        solicitud=datos,
        fecha_actual=datetime.now().strftime("%Y-%m-%d %H:%M"),
        aprobador=aprobador,
        jefe_unidad=jefe_unidad,
    )
    return html


# --- Selector de plantilla por tipo ---
def generar_pdf_por_tipo(sol, det, admin=None):
    tipo = (sol or {}).get('tipo', 'crear')

    if tipo == 'eliminar':
        aprobador = None
        if admin:
            aprobador = {
                "nombre": f"{admin.get('nombre','')} {admin.get('apellido','')}".strip(),
                "cargo": "Administrador de Infraestructura",
            }
        jefe_unidad = {
            "nombre": (det or {}).get("firma_jefe") or "",
            "cargo":  (det or {}).get("cargo_jefe") or "",
        }
        return render_template(
            "pdf_eliminacion.html",
            solicitud=sol,
            detalle=det or {},
            aprobador=aprobador,
            jefe_unidad=jefe_unidad,
            fecha_actual=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    if tipo == 'recursos':
        jefe_unidad = {
            "nombre": (det or {}).get("firma_jefe") or "",
            "cargo":  (det or {}).get("cargo_jefe") or "",
        }
        aprobador = None
        if admin:
            aprobador = {
                "nombre": f"{admin.get('nombre','')} {admin.get('apellido','')}".strip(),
                "cargo": "Administrador de Infraestructura",
            }
        return render_template(
            "pdf_recurso.html",           # <-- tu plantilla de recursos
            solicitud=sol,
            detalle=det or {},
            jefe_unidad=jefe_unidad,
            aprobador=aprobador,
            fecha_actual=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    # fallback a "crear"
    return generar_pdf_solicitud(sol, det, admin)






# Iniciar servidor
#if __name__ == '__main__':
#   app.run(debug=True, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    print("Iniciando Flask…")
    app.run(host="127.0.0.1", port=5000, debug=True)



application = app


