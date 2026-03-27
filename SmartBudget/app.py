from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "smartbudget_secret_key"

DB_NAME = "database.db"

# Створення бд и таблиць
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        conn.close()

init_db()

# головна сторінка
@app.route("/")
def index():
    return render_template("index.html")

# Регістрація
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Реєстрація успішна!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Користувач вже існує!", "danger")
        finally:
            conn.close()
    return render_template("register.html")

# Логін
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
           
            session['user_id'] = user[0]
            return redirect(url_for("dashboard", user_id=user[0]))
        else:
            flash("Невірний логін або пароль", "danger")
    return render_template("login.html")

# Дашборд
@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE user_id=?", (user_id,))
    transactions = cursor.fetchall()
    conn.close()
    balance = sum(t[4] if t[2] == "income" else -t[4] for t in transactions)
    return render_template("dashboard.html", transactions=transactions, balance=balance, user_id=user_id)

# Додавання транзакцій
@app.route("/add_transaction/<int:user_id>", methods=["POST"])
def add_transaction(user_id):
    t_type = request.form["type"]
    category = request.form["category"]
    amount = float(request.form["amount"])
    date = request.form["date"]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, t_type, category, amount, date)
    )
    conn.commit()
    conn.close()
    flash("Транзакція додана!", "success")
    return redirect(url_for("dashboard", user_id=user_id))

# Для зміни типу транзакціі
@app.route('/toggle/<int:id>', methods=['POST'])
def toggle_transaction(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT type, user_id FROM transactions WHERE id=?", (id,))
    t = cursor.fetchone()
    if t:
        current_type, user_id = t
        new_type = 'income' if current_type == 'expense' else 'expense'
        cursor.execute("UPDATE transactions SET type=? WHERE id=?", (new_type, id))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard', user_id=user_id))

if __name__ == "__main__":
    app.run(debug=True)
