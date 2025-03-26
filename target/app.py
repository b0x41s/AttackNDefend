import os
import sqlite3
import uuid
from flask import Flask, request, session, render_template, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flags (id INTEGER PRIMARY KEY, flag TEXT)')
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('admin', 'password123'))
    c.execute('INSERT OR IGNORE INTO flags VALUES (1, ?)', ('FLAG{initial_flag}',))
    conn.commit()
    conn.close()

def login(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    c.execute(query)
    result = c.fetchone()
    conn.close()
    return result is not None

def generate_flag():
    return f"FLAG{{{uuid.uuid4()}}}"

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_route():
    username = request.form['username']
    password = request.form['password']
    if login(username, password):
        session['logged_in'] = True
        return "Login succesvol"
    return "Login mislukt", 401

@app.route('/get_flag')
def get_flag():
    if 'logged_in' not in session:
        return "Unauthorized", 403
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT flag FROM flags WHERE id = 1')
    flag = c.fetchone()[0]
    conn.close()
    return flag

@app.route('/set_flag', methods=['POST'])
def set_flag():
    new_flag = generate_flag()
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO flags (id, flag) VALUES (1, ?)', (new_flag,))
    conn.commit()
    conn.close()
    return "Flag ingesteld"

@app.route('/health')
def health():
    return "OK"

@app.route('/editor', methods=['GET', 'POST'])
def editor():
    if request.method == 'POST':
        new_code = request.form['code']
        with open('app.py', 'w') as f:
            f.write(new_code)
        return "Code opgeslagen"
    with open('app.py', 'r') as f:
        code = f.read()
    return render_template('editor.html', code=code)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)