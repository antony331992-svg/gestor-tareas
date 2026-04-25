from flask import Flask, render_template, request, redirect, session
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = "clave_secreta_123"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            completada INTEGER DEFAULT 0,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def inicio():
    if "usuario_id" not in session:
        return redirect("/login")
    conn = get_db()
    tareas = conn.execute("SELECT * FROM tareas WHERE usuario_id = ?",
                          (session["usuario_id"],)).fetchall()
    conn.close()
    return render_template("index.html", tareas=tareas)

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if len(password) < 8:
            return render_template("registro.html", error="La contraseña debe tener al menos 8 caracteres")
        if not any(c.isupper() for c in password):
            return render_template("registro.html", error="La contraseña debe tener al menos una mayúscula")
        if not any(c.isdigit() for c in password):
            return render_template("registro.html", error="La contraseña debe tener al menos un número")
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        try:
            conn = get_db()
            conn.execute("INSERT INTO usuarios (email, password) VALUES (?, ?)",
                         (email, password_hash))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            return render_template("registro.html", error="Este email ya está registrado")
    return render_template("registro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        usuario = conn.execute("SELECT * FROM usuarios WHERE email = ?",
                               (email,)).fetchone()
        conn.close()
        if usuario and bcrypt.checkpw(password.encode("utf-8"), usuario["password"]):
            session["usuario_id"] = usuario["id"]
            return redirect("/")
        return render_template("login.html", error="Email o contraseña incorrectos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/crear", methods=["POST"])
def crear():
    titulo = request.form["titulo"]
    descripcion = request.form["descripcion"]
    conn = get_db()
    conn.execute("INSERT INTO tareas (titulo, descripcion, usuario_id) VALUES (?, ?, ?)",
                 (titulo, descripcion, session["usuario_id"]))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db()
    conn.execute("DELETE FROM tareas WHERE id = ? AND usuario_id = ?",
                 (id, session["usuario_id"]))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/completar/<int:id>", methods=["POST"])
def completar(id):
    conn = get_db()
    conn.execute("UPDATE tareas SET completada = 1 WHERE id = ? AND usuario_id = ?",
                 (id, session["usuario_id"]))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/editar/<int:id>")
def editar(id):
    conn = get_db()
    tarea = conn.execute("SELECT * FROM tareas WHERE id = ? AND usuario_id = ?",
                         (id, session["usuario_id"])).fetchone()
    conn.close()
    return render_template("editar.html", tarea=tarea)

@app.route("/editar/<int:id>", methods=["POST"])
def editar_guardar(id):
    titulo = request.form["titulo"]
    descripcion = request.form["descripcion"]
    conn = get_db()
    conn.execute("UPDATE tareas SET titulo = ?, descripcion = ? WHERE id = ? AND usuario_id = ?",
                 (titulo, descripcion, id, session["usuario_id"]))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)