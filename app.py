from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

# Функция для проверки пользователя в базе данных
def check_user(username, password):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {'id': user[0], 'username': user[1], 'role': user[3]}  # Возвращаем данные с ролью
        return None
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

        # Проверяем пользователя
        user = check_user(username, password)
        if user:
            # В зависимости от роли перенаправляем на разные страницы
            if user['role'] == 'supplier':
                return redirect(url_for('supplier_page'))
            elif user['role'] == 'business':
                return redirect(url_for('business_page'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

# Страница для поставщиков
@app.route('/supplier', methods=['GET'])
def supplier_page():
    return render_template('mainSupply.html')  # Шаблон для поставщиков

# Страница для бизнеса
@app.route('/business', methods=['GET'])
def business_page():
    return render_template('mainBusiness.html')  # Шаблон для бизнеса

@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.json
    name = data.get('name')
    quantity = data.get('quantity')
    price = data.get('price')

    if name and quantity and price:
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cards (name, quantity, price)
                VALUES (?, ?, ?)
            ''', (name, quantity, float(price)))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Card added successfully!'}), 200
        except Exception as e:
            print(f"Ошибка при сохранении карточки: {e}")
            return jsonify({'message': 'Error saving card to database.'}), 500
    return jsonify({'message': 'Invalid data!'}), 400

if __name__ == '__main__':
    app.run(debug=True)