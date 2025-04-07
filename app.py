from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "23260504hAv",
    "dbname": "sto_bot"
}

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'logged_in' not in session:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Неверный логин или пароль")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, phone, car, problem, preferred_datetime, created_at
        FROM service_requests ORDER BY created_at DESC
    """)
    requests = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", requests=requests)

@app.route("/delete/<int:req_id>")
def delete(req_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM service_requests WHERE id = %s", (req_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

@app.route("/edit/<int:req_id>", methods=["GET", "POST"])
def edit(req_id):
    conn = get_connection()
    cur = conn.cursor()
    if request.method == "POST":
        name = request.form['name']
        phone = request.form['phone']
        car = request.form['car']
        problem = request.form['problem']
        datetime = request.form['datetime']
        cur.execute("""
            UPDATE service_requests
            SET name=%s, phone=%s, car=%s, problem=%s, preferred_datetime=%s
            WHERE id=%s
        """, (name, phone, car, problem, datetime, req_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    cur.execute("SELECT id, name, phone, car, problem, preferred_datetime FROM service_requests WHERE id = %s", (req_id,))
    data = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("edit.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)