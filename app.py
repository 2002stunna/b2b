from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
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

# Функция для получения карточек конкретного поставщика
def get_cards_by_supplier(supplier_id):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE supplier_id = ?', (supplier_id,))
        cards = cursor.fetchall()
        conn.close()
        return cards
    except Exception as e:
        print(f"Ошибка при получении карточек поставщика: {e}")
        return []

# Функция для сохранения карточки в базе данных
def save_card_to_db(name, quantity, price, supplier_id):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cards (name, quantity, price, supplier_id)
            VALUES (?, ?, ?, ?)
        ''', (name, quantity, price, supplier_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при сохранении карточки: {e}")

# Главная страница для входа
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Both fields are required!", username=None)

        user = check_user(username, password)
        if user:
            response = make_response(redirect(url_for('supplier_page') if user['role'] == 'supplier' else url_for('business_page')))
            response.set_cookie('username', username)  # Устанавливаем cookie
            response.set_cookie('password', password)  # Устанавливаем cookie
            return response
        else:
            return render_template('login.html', error="Invalid username or password", username=None)

    return render_template('login.html', username=None)

# Страница для поставщика
@app.route('/supplier', methods=['GET', 'POST'])
def supplier_page():
    # Получаем логин пользователя из cookie
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'supplier':
        return redirect(url_for('login'))

    supplier_id = user['id']

    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        if name and quantity and price:
            save_card_to_db(name, quantity, float(price), supplier_id)
            return redirect(url_for('supplier_page'))
        else:
            cards = get_cards_by_supplier(supplier_id)
            return render_template('mainSupply.html', cards=cards, error="All fields are required!", username=username)

    cards = get_cards_by_supplier(supplier_id)
    return render_template('mainSupply.html', cards=cards, username=username)

# Страница для покупателя
@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    cards = get_cards()
    return render_template('mainBusiness.html', cards=cards, username=username)

# API для получения карточек
@app.route('/api/cards', methods=['GET'])
def api_get_cards():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')
        cards = cursor.fetchall()
        conn.close()

        cards_list = [{'id': card[0], 'name': card[1], 'quantity': card[2], 'price': card[3]} for card in cards]
        return jsonify(cards_list), 200
    except Exception as e:
        print(f"Ошибка при получении карточек через API: {e}")
        return jsonify({'error': 'Failed to fetch cards'}), 500

if __name__ == '__main__':
    app.run(debug=True)