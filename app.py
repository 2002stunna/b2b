from flask import Flask, request, render_template, redirect, url_for, make_response
import sqlite3

app = Flask(__name__)

# Проверка пользователя в базе данных
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

# Получение карточек текущего поставщика
def get_cards_by_supplier(supplier_id):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE supplier_id = ?', (supplier_id,))
        cards = cursor.fetchall()
        conn.close()

        # Преобразуем результат выборки в список словарей
        return [{'id': card[0], 'name': card[1], 'quantity': card[2], 'price': card[3]} for card in cards]
    except Exception as e:
        print(f"Ошибка при получении карточек поставщика: {e}")
        return []

# Сохранение карточки в базе данных
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
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response
        else:
            return render_template('login.html', error="Invalid username or password", username=None)

    return render_template('login.html', username=None)

@app.route('/supplier', methods=['GET', 'POST'])
def supplier_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'supplier':
        return redirect(url_for('login'))

    supplier_id = user['id']
    print(f"[DEBUG] Текущий поставщик ID: {supplier_id}")  # Отладка

    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        print(f"[DEBUG] Добавляем товар: {name}, {quantity}, {price}, Поставщик: {supplier_id}")  # Отладка

        if name and quantity and price:
            save_card_to_db(name, quantity, float(price), supplier_id)
            return redirect(url_for('supplier_page'))

    cards = get_cards_by_supplier(supplier_id)
    print(f"[DEBUG] Карточки для поставщика {supplier_id}: {cards}")  # Отладка

    return render_template('mainSupply.html', cards=cards, username=username)

@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')
        cards = cursor.fetchall()
        conn.close()
        if not cards:
            print("[DEBUG] Нет карточек в базе данных.")
    except Exception as e:
        print(f"[ERROR] Ошибка при получении карточек: {e}")
        cards = []

    return render_template('mainBusiness.html', cards=cards, username=username)

if __name__ == '__main__':
    app.run(debug=True)