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

# Ruta de prueba para ver usuarios
@app.route('/usuarios')
def usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return '<br>'.join([f"{u[1]} ({u[4]})" for u in usuarios])

# Página de login para administrador
@app.route('/login_admin')
def login_admin():
    return render_template('login_admin.html')

# Verificar login del administrador
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

# Dashboard del administrador
@app.route('/dashboard_admin')
def dashboard_admin():
    return render_template('dashboard_admin.html')

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

        # Verificar si ya existe el solicitante
        cursor.execute("SELECT * FROM solicitantes WHERE nombre=%s AND apellido=%s AND correo=%s", 
                       (nombre, apellido, correo))
        solicitante = cursor.fetchone()

        # Si no existe, lo insertamos
        if not solicitante:
            cursor.execute("INSERT INTO solicitantes (nombre, apellido, correo) VALUES (%s, %s, %s)", 
                           (nombre, apellido, correo))
            conn.commit()
            cursor.execute("SELECT * FROM solicitantes WHERE nombre=%s AND apellido=%s AND correo=%s", 
                           (nombre, apellido, correo))
            solicitante = cursor.fetchone()

        conn.close()

        # Si existe o se creó, iniciamos sesión
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

    # Asegura que los valores no sean None
    nombre = usuario[0] if usuario[0] else ""
    apellido = usuario[1] if usuario[1] else ""

    nombre_completo = f"{nombre} {apellido}".strip()

    return render_template('dashboard_solicitante.html', nombre=nombre_completo)

@app.route('/historial_solicitante')
def historial():
    # Solo para evitar el error, luego lo implementas bien
    return "<h2>En construcción... Aquí irá tu historial de solicitudes.</h2>"


# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True)


@app.route('/dashboard_admin')
def dashboard_admin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, fecha, estado FROM solicitudes ORDER BY fecha DESC")
    solicitudes = cursor.fetchall()
    conn.close()
    return render_template('dashboard_admin.html', solicitudes=solicitudes)

@app.route("/enviado")
def enviado():
    return render_template("enviado.html")







