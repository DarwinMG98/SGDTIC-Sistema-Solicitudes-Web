from flask import Flask, render_template,redirect, request, session, url_for
import pymysql

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'


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
        cursor.execute("SELECT * FROM usuarios WHERE nombre=%s AND apellido=%s AND correo=%s AND rol='solicitante'", 
                       (nombre, apellido, correo))
        solicitante = cursor.fetchone()
        conn.close()

        if solicitante:
            session['usuario_id'] = solicitante[0]
            return redirect(url_for('dashboard_solicitante'))
        else:
            return "Credenciales incorrectas o no es solicitante"
    return render_template('login_solicitante.html')

@app.route('/dashboard_solicitante')
def dashboard_solicitante():
    return render_template('dashboard_solicitante.html')



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



