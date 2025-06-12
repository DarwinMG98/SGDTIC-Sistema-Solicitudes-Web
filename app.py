from flask import Flask, render_template,redirect, request, session, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import pymysql

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from datetime import datetime

@app.route("/crear_solicitud", methods=["GET", "POST"])
def crear_solicitud():
    if request.method == "POST":
        tipo = request.form.get('tipo')
        observaciones = request.form.get('observaciones')
        usuario_id = session.get('usuario_id')
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
        vcpu = request.form['vcpu']
        ram = request.form['ram']
        disco_sistema = request.form['disco_sistema']
        disco_datos = request.form['disco_datos']
        vida_util = request.form['vida_util']
        justificacion_recursos = request.form['justificacion_recursos']
        accesos = request.form['accesos']
        responsable_aplicacion = request.form['responsable_aplicacion']
        unidad_responsable = request.form['unidad_responsable']
        contacto_soporte = request.form['contacto_soporte']
        observaciones_adicionales = request.form['observaciones']   # puede ser otro campo
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
        SELECT id, tipo, fecha_solicitud, estado
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


    conn.close()

    print(detalle)

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
    
    return render_template(
        'revisar_solicitud.html',
        solicitud=solicitud,
        detalle=detalle
     )

@app.route('/editar_solicitud/<int:id>', methods=['GET', 'POST'])
def editar_solicitud(id):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)


    cursor.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
    solicitud = cursor.fetchone()

    cursor.execute("SELECT * FROM solicitud_detalle WHERE solicitud_id=%s", (id,))
    detalle = cursor.fetchone()

    if request.method == "POST":

        nombre_completo = request.form['nombre_completo']
        unidad = request.form['unidad']
        correo = request.form['correo']
        telefono = request.form['telefono']
        responsable_tecnico = request.form['responsable_tecnico']

        origen_solicitud = request.form['origen_solicitud']
        anteproyecto = request.form['anteproyecto']
        motivo = request.form['motivo']
        tipo_servidor = request.form['tipo_servidor']
        sistema_operativo = request.form['sistema_operativo']
        version_so = request.form['version_so']
        vcpu = request.form['vcpu']
        ram = request.form['ram']
        disco_sistema = request.form['disco_sistema']
        disco_datos = request.form['disco_datos']
        vida_util = request.form['vida_util']
        justificacion_recursos = request.form['justificacion_recursos']
        accesos = request.form['accesos']
        responsable_aplicacion = request.form['responsable_aplicacion']
        unidad_responsable = request.form['unidad_responsable']
        contacto_soporte = request.form['contacto_soporte']
        observaciones_adicionales = request.form['observaciones_adicionales']
        firma_solicitante = request.form['firma_solicitante']
        cargo_solicitante = request.form['cargo_solicitante']
        firma_jefe = request.form['firma_jefe']
        cargo_jefe = request.form['cargo_jefe']

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
        conn.commit()
        conn.close()
        return redirect(url_for("historial"))

    conn.close()

    return render_template("formulario_editar.html", detalle=detalle, observacion=solicitud['observaciones'])



# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True)







