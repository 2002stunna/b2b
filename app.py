from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

# Функция для проверки пользователя в базе данных
def check_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Главная страница с формой логина
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_user(username, password):
            return redirect(url_for('success'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

# Страница успешного входа
@app.route('/success')
def success():
    render_template('main.html')
    
if __name__ == '__main__':
    app.run(debug=True)