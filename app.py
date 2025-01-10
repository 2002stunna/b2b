from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
import sqlite3

app = Flask(__name__)

# ---------------------- 1. Проверка пользователя (прежнее) ----------------------
def check_user(username, password):
    try:
        conn = sqlite3.connect('Main.db')
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

# ---------------------- 2. Сохранение заявки (pending_users) ----------------------
def save_pending_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pending_users
            (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при сохранении пользователя в pending_users: {e}")
        return False

# ---------------------- 3. Перенести заявку из pending_users в users ----------------------
def approve_pending_user(pending_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        # 1. Получаем запись
        cursor.execute('SELECT * FROM pending_users WHERE id=?', (pending_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return "Заявка не найдена."

        # row: (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
        # 2. Переносим в таблицу users
        cursor.execute('''
            INSERT INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))

        # 3. Удаляем из pending_users
        cursor.execute('DELETE FROM pending_users WHERE id=?', (pending_id,))
        conn.commit()
        conn.close()
        return "Заявка одобрена и пользователь добавлен в базу."
    except Exception as e:
        return f"Ошибка при одобрении заявки: {e}"

# ---------------------- 4. Отклонить заявку (просто удалить) ----------------------
def reject_pending_user(pending_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pending_users WHERE id=?', (pending_id,))
        conn.commit()
        conn.close()
        return "Заявка отклонена и удалена."
    except Exception as e:
        return f"Ошибка при отклонении заявки: {e}"

# ---------------------- 5. Получение всех карточек (прежнее) ----------------------
def get_all_cards():
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')
        cards = cursor.fetchall()
        conn.close()
        return [{'id': card[0], 'name': card[1], 'quantity': card[2], 'price': card[3]} for card in cards]
    except Exception as e:
        print(f"Ошибка при получении всех карточек: {e}")
        return []

# ---------------------- 6. Получение карточек текущего поставщика (прежнее) ----------------------
def get_cards_by_supplier(supplier_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE supplier_id = ?', (supplier_id,))
        cards = cursor.fetchall()
        conn.close()
        return [{'id': card[0], 'name': card[1], 'quantity': card[2], 'price': card[3]} for card in cards]
    except Exception as e:
        print(f"Ошибка при получении карточек поставщика: {e}")
        return []

# ---------------------- 7. Сохранение карточки (прежнее) ----------------------
def save_card_to_db(name, quantity, price, supplier_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
                       (name, quantity, price, supplier_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при сохранении карточки: {e}")

# ---------------------- 8. Получение данных аккаунта пользователя (прежнее) ----------------------
def get_user_account(username):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT LegalName, INN, KPP, OGRN, LegalAddress, Contact
            FROM users
            WHERE username = ?
        ''', (username,))
        account_data = cursor.fetchone()
        conn.close()
        return account_data
    except Exception as e:
        print(f"Ошибка при получении данных аккаунта: {e}")
        return None

# ---------------------- 9. Маршрут: LOGIN (добавлен вариант role=security) ----------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Both fields are required!", username=None)

        user = check_user(username, password)
        if user:
            # В зависимости от роли - перенаправляем
            if user['role'] == 'supplier':
                response = make_response(redirect(url_for('supplier_page')))
            elif user['role'] == 'security':
                response = make_response(redirect(url_for('security_service')))
            else:
                response = make_response(redirect(url_for('business_page')))

            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response
        else:
            return render_template('login.html', error="Invalid username or password", username=None)

    return render_template('login.html', username=None)

# ---------------------- 10. Маршрут: SUPPLIER (прежнее) ----------------------
@app.route('/supplier', methods=['GET', 'POST'])
def supplier_page():
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

    cards = get_cards_by_supplier(supplier_id)
    return render_template('mainSupply.html', cards=cards, username=username)

# ---------------------- 11. Маршрут: BUSINESS (прежнее) ----------------------
@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    return render_template('mainBusiness.html', username=username)

# ---------------------- 12. API для карточек (прежнее) ----------------------
@app.route('/api/cards', methods=['GET'])
def api_cards():
    try:
        cards = get_all_cards()
        return jsonify(cards)
    except Exception as e:
        print(f"Ошибка при получении карточек через API: {e}")
        return jsonify({'error': 'Failed to fetch cards'}), 500

# ---------------------- 13. Страница аккаунта поставщика (прежнее) ----------------------
@app.route('/supplier/account', methods=['GET'])
def supplier_account():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'supplier':
        return redirect(url_for('login'))

    account_data = get_user_account(username)
    if not account_data:
        return render_template('mainAccount.html', error="Account data not found.", username=username)

    return render_template(
        'mainAccount.html',
        username=username,
        legal_name=account_data[0],
        inn=account_data[1],
        kpp=account_data[2],
        ogrn=account_data[3],
        legal_address=account_data[4],
        contact=account_data[5]
    )

# ---------------------- 14. Регистрация: сохраняем в pending_users ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        legal_name = request.form.get('legal_name')
        inn = request.form.get('inn')
        kpp = request.form.get('kpp')
        ogrn = request.form.get('ogrn')
        legal_address = request.form.get('legal_address')
        contact = request.form.get('contact')

        if not all([username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact]):
            return render_template('Registration.html', error="All fields are required!")

        # Сохраняем заявку в pending_users
        success = save_pending_user(
            username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact
        )
        if success:
            return render_template('Registration.html', success_message="Ожидайте подтверждения заявки")
        else:
            return render_template('Registration.html', error="Ошибка при сохранении заявки")

    return render_template('Registration.html')

# ---------------------- 15. Страница SecurityService (GET) - показывает pending_users ----------------------
@app.route('/security-service', methods=['GET', 'POST'])
def security_service():
    # Проверяем, что пользователь - security
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    # Читаем pending_users
    message = request.args.get('message')
    conn = sqlite3.connect('Main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pending_users')
    pending_list = cursor.fetchall()
    conn.close()

    # pending_list => [(id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact), ...]
    return render_template('SecurityService.html', pending_list=pending_list, message=message)

# ---------------------- 16. Одобрить заявку (POST) ----------------------
@app.route('/approve-pending', methods=['POST'])
def approve_pending():
    # Проверяем security
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    pending_id = request.form.get('pending_id')
    if not pending_id:
        return redirect(url_for('security_service'))

    result_msg = approve_pending_user(pending_id)
    return redirect(url_for('security_service', message=result_msg))

# ---------------------- 17. Отклонить заявку (POST) ----------------------
@app.route('/reject-pending', methods=['POST'])
def reject_pending():
    # Проверяем security
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    pending_id = request.form.get('pending_id')
    if not pending_id:
        return redirect(url_for('security_service'))

    result_msg = reject_pending_user(pending_id)
    return redirect(url_for('security_service', message=result_msg))

# ---------------------- 18. Точка входа ----------------------
if __name__ == '__main__':
    app.run(debug=True)