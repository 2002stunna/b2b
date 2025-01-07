from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

def check_user(username, password):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"Ошибка в check_user: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Ошибка: не заполнены поля логина или пароля.", 400

        if check_user(username, password):
            return redirect(url_for('success'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/success', methods=['GET'])
def success():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True)