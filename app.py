from flask import Flask, request, render_template, redirect, url_for, jsonify
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

# Функция для получения всех карточек
def get_cards():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')  # Получаем все карточки
        cards = cursor.fetchall()
        conn.close()
        return cards
    except Exception as e:
        print(f"Ошибка при получении карточек: {e}")
        return []

# Функция для сохранения карточки в базе данных
def save_card_to_db(name, quantity, price):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cards (name, quantity, price)
            VALUES (?, ?, ?)
        ''', (name, quantity, price))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при сохранении карточки: {e}")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Both fields are required!")

        user = check_user(username, password)
        if user:
            if user['role'] == 'supplier':
                return redirect(url_for('supplier_page'))
            elif user['role'] == 'business':
                return redirect(url_for('business_page'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/supplier', methods=['GET', 'POST'])
def supplier_page():
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        if name and quantity and price:
            save_card_to_db(name, quantity, float(price))
            return redirect(url_for('supplier_page'))
        else:
            cards = get_cards()
            return render_template('mainSupply.html', cards=cards, error="All fields are required!")

    cards = get_cards()
    return render_template('mainSupply.html', cards=cards)

@app.route('/business')
def business_page():
    return render_template('mainBusiness.html')

@app.route('/api/cards', methods=['GET'])
def api_get_cards():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')
        cards = cursor.fetchall()
        conn.close()

        # Преобразуем карточки в список словарей для передачи в JSON
        cards_list = [{'id': card[0], 'name': card[1], 'quantity': card[2], 'price': card[3]} for card in cards]
        return jsonify(cards_list), 200
    except Exception as e:
        print(f"Ошибка при получении карточек через API: {e}")
        return jsonify({'error': 'Failed to fetch cards'}), 500

if __name__ == '__main__':
    app.run(debug=True)