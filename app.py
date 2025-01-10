from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
import sqlite3

app = Flask(__name__)


# -----------------------------------------------------------------------------
# 1. Проверка пользователя (как было)
# -----------------------------------------------------------------------------
def check_user(username, password):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {'id': user[0], 'username': user[1], 'role': user[3]}
        return None
    except Exception as e:
        print(f"Ошибка в check_user: {e}")
        return None

# -----------------------------------------------------------------------------
# 2. Сохранение заявки
# -----------------------------------------------------------------------------
def save_pending_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    """
    Сохраняем в таблицу pending_users, статус по умолчанию 'pending'.
    Возвращаем ID новой записи, чтобы фронт мог отслеживать состояние.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pending_users
            (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact))
        new_id = cursor.lastrowid  # ID добавленной записи
        conn.commit()
        conn.close()
        return new_id
    except Exception as e:
        print(f"Ошибка при сохранении пользователя в pending_users: {e}")
        return None  # Вернём None, если не удалось

# -----------------------------------------------------------------------------
# 3. Обновить статус заявки (pending -> approved/rejected)
# -----------------------------------------------------------------------------
def update_pending_status(pending_id, new_status):
    """
    Устанавливаем status='approved' или 'rejected' в pending_users
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE pending_users SET status=? WHERE id=?', (new_status, pending_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении статуса заявки: {e}")
        return False

# -----------------------------------------------------------------------------
# 4. Перенести запись (при approve) в users
# -----------------------------------------------------------------------------
def move_to_users(pending_id):
    """
    Берём запись из pending_users, переносим в users.
    НЕ удаляем, а только ставим status='approved', чтобы пользователь мог отследить.
    (Если хотите удалять, можно cursor.execute('DELETE FROM pending_users ...')
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM pending_users WHERE id=?', (pending_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Не найдена заявка"

        # row = (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact, status)
        # Вставим в users
        cursor.execute('''
            INSERT INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))

        conn.commit()
        conn.close()
        return True, "Пользователь добавлен в таблицу users"
    except Exception as e:
        print(f"Ошибка при переносе в users: {e}")
        return False, str(e)

# -----------------------------------------------------------------------------
# 5. Получение статуса заявки
# -----------------------------------------------------------------------------
def get_pending_status(pending_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM pending_users WHERE id=?', (pending_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Ошибка в get_pending_status: {e}")
        return None

# -----------------------------------------------------------------------------
# 6. Получение всех карточек (старый код)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 7. Получение карточек поставщика (старый код)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 8. Сохранение карточки (старый код)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 9. Данные аккаунта (старый код)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 10. Логин (добавлена ветка security)
# -----------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Both fields are required!", username=None)

        user = check_user(username, password)
        if user:
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

# -----------------------------------------------------------------------------
# 11. Страница поставщика
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 12. Страница бизнес-пользователя
# -----------------------------------------------------------------------------
@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    return render_template('mainBusiness.html', username=username)

# -----------------------------------------------------------------------------
# 13. API для карточек
# -----------------------------------------------------------------------------
@app.route('/api/cards', methods=['GET'])
def api_cards():
    try:
        cards = get_all_cards()
        return jsonify(cards)
    except Exception as e:
        print(f"Ошибка при получении карточек через API: {e}")
        return jsonify({'error': 'Failed to fetch cards'}), 500

# -----------------------------------------------------------------------------
# 14. Аккаунт поставщика
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 15. Регистрация: возвращаем pending_id
# -----------------------------------------------------------------------------
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

        new_id = save_pending_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact)
        if new_id is None:
            return render_template('Registration.html', error="Ошибка при сохранении заявки")
        
        # Если всё успешно, возвращаем страницу, но передаём pending_id
        return render_template('Registration.html', pending_id=new_id)
    return render_template('Registration.html')

# -----------------------------------------------------------------------------
# 16. Маршрут для проверки статуса заявки (AJAX)
# -----------------------------------------------------------------------------
@app.route('/check_status/<int:pending_id>', methods=['GET'])
def check_status(pending_id):
    status = get_pending_status(pending_id)
    if status is None:
        return jsonify({'status': 'not_found'}), 404
    return jsonify({'status': status})

# -----------------------------------------------------------------------------
# 17. Страница SecurityService: показываем все поля
# -----------------------------------------------------------------------------
@app.route('/security-service')
def security_service():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    message = request.args.get('message')

    conn = sqlite3.connect('Main.db')
    cursor = conn.cursor()
    # Получаем ВСЁ из pending_users (включая status)
    cursor.execute('SELECT * FROM pending_users')
    pending_list = cursor.fetchall()
    conn.close()

    # row структура: 
    # (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact, status)

    return render_template('SecurityService.html', pending_list=pending_list, message=message)

# -----------------------------------------------------------------------------
# 18. Одобрить заявку (status = approved) и перенос в users
# -----------------------------------------------------------------------------
@app.route('/approve-pending', methods=['POST'])
def approve_pending():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    pending_id = request.form.get('pending_id')
    if not pending_id:
        return redirect(url_for('security_service'))

    # 1. Меняем статус на approved
    ok = update_pending_status(pending_id, 'approved')
    if not ok:
        return redirect(url_for('security_service', message="Ошибка при обновлении статуса"))

    # 2. Переносим в users
    success, msg = move_to_users(pending_id)
    if not success:
        return redirect(url_for('security_service', message=msg))

    return redirect(url_for('security_service', message="Заявка одобрена!"))

# -----------------------------------------------------------------------------
# 19. Отклонить заявку (status = rejected)
# -----------------------------------------------------------------------------
@app.route('/reject-pending', methods=['POST'])
def reject_pending():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    pending_id = request.form.get('pending_id')
    if not pending_id:
        return redirect(url_for('security_service'))

    # Просто ставим статус = rejected (или можно удалить)
    ok = update_pending_status(pending_id, 'rejected')
    if not ok:
        return redirect(url_for('security_service', message="Ошибка при отклонении заявки"))

    return redirect(url_for('security_service', message="Заявка отклонена."))

# -----------------------------------------------------------------------------
# 20. Запуск
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)