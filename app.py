from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
import sqlite3

app = Flask(__name__)

# ----------------- 1. Проверка пользователя ------------------
def check_user(username, password):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            # row = (id, username, password, role, LegalName, ...)
            return {'id': row[0], 'username': row[1], 'role': row[3]}
        return None
    except Exception as e:
        print("Ошибка check_user:", e)
        return None

# ----------------- 2. Pending users (заявки) операции ------------------
def get_all_pending():
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pending_users')
        rows = cursor.fetchall()
        conn.close()
        return rows  # (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact, status)
    except Exception as e:
        print("Ошибка get_all_pending:", e)
        return []

def update_pending_status(pending_id, new_status):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE pending_users SET status=? WHERE id=?', (new_status, pending_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка update_pending_status:", e)
        return False

def move_pending_to_users(pending_id):
    """Перенести запись из pending_users в users (по заявке)."""
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        # Получим запись
        cursor.execute('SELECT * FROM pending_users WHERE id=?', (pending_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Заявка не найдена"

        # row = (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact, status)
        cursor.execute('''
            INSERT INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
        conn.commit()
        conn.close()
        return True, "Пользователь добавлен"
    except Exception as e:
        print("Ошибка move_pending_to_users:", e)
        return False, str(e)

# ----------------- 3. Users (основная таблица) операции ------------------
def get_all_users():
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        rows = cursor.fetchall()
        conn.close()
        return rows  # (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
    except Exception as e:
        print("Ошибка get_all_users:", e)
        return []

def add_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка add_user:", e)
        return False

def update_user(user_id, username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET username=?, password=?, role=?, LegalName=?, INN=?, KPP=?, OGRN=?, LegalAddress=?, Contact=?
            WHERE id=?
        ''', (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка update_user:", e)
        return False

def delete_user(user_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка delete_user:", e)
        return False

# ----------------- 4. Работа с карточками ------------------
def get_all_cards():
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')
        cards = cursor.fetchall()
        conn.close()
        return [{'id': c[0], 'name': c[1], 'quantity': c[2], 'price': c[3]} for c in cards]
    except Exception as e:
        print("Ошибка get_all_cards:", e)
        return []

def get_cards_by_supplier(supplier_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE supplier_id=?', (supplier_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'name': r[1], 'quantity': r[2], 'price': r[3]} for r in rows]
    except Exception as e:
        print("Ошибка get_cards_by_supplier:", e)
        return []

def save_card_to_db(name, quantity, price, supplier_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)',
                       (name, quantity, price, supplier_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Ошибка save_card_to_db:", e)

# ----------------- 5. Получение информации об аккаунте ------------------
def get_user_account(username):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT LegalName, INN, KPP, OGRN, LegalAddress, Contact FROM users WHERE username=?', (username,))
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        print("Ошибка get_user_account:", e)
        return None

# ----------------- 6. ДОПОЛНИТЕЛЬНО: Получение карточки по id ------------------
def get_card_by_id(card_id):
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE id=?', (card_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'quantity': row[2],
                'price': row[3],
                'supplier_id': row[4]
            }
        return None
    except Exception as e:
        print("Ошибка get_card_by_id:", e)
        return None

# >>> НОВЫЙ ФУНКЦИОНАЛ >>>
# Функции для работы с заявками (orders)

def create_order(card_id, buyer_id, desired_qty):
    """
    Создание заявки на покупку.
    Добавляется запись в таблицу orders с полями:
    (id, card_id, buyer_id, desired_qty, status)
    status по умолчанию 'pending'
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (card_id, buyer_id, desired_qty, status)
            VALUES (?, ?, ?, ?)
        ''', (card_id, buyer_id, desired_qty, 'pending'))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка create_order:", e)
        return False

def get_orders_by_supplier(supplier_id):
    """
    Получение заявок для товаров конкретного поставщика.
    Производится JOIN с таблицей users для получения имени покупателя.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, u.username, o.desired_qty, o.status, c.name
            FROM orders o
            JOIN users u ON o.buyer_id = u.id
            JOIN cards c ON o.card_id = c.id
            WHERE c.supplier_id = ?
        ''', (supplier_id,))
        rows = cursor.fetchall()
        conn.close()
        # Возвращаем список словарей
        return [{'order_id': r[0], 'buyer': r[1], 'desired_qty': r[2], 'status': r[3], 'product_name': r[4]} for r in rows]
    except Exception as e:
        print("Ошибка get_orders_by_supplier:", e)
        return []

def update_order_status(order_id, new_status):
    """
    Обновление статуса заявки.
    new_status может быть 'approved' или 'rejected'.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status=? WHERE id=?', (new_status, order_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка update_order_status:", e)
        return False

def update_card_quantity(card_id, delta):
    """
    Изменение количества товара на складе на величину delta (может быть отрицательным).
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM cards WHERE id=?', (card_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        new_quantity = row[0] + delta
        if new_quantity < 0:
            conn.close()
            return False
        cursor.execute('UPDATE cards SET quantity=? WHERE id=?', (new_quantity, card_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка update_card_quantity:", e)
        return False

# Новый маршрут для поставщика: просмотр заявок
@app.route('/supplier/orders', methods=['GET', 'POST'])
def supplier_orders():
    """
    На этой странице поставщика отображаются заявки покупателей.
    Для каждой заявки выводится имя покупателя, название товара, желаемое количество
    и кнопки для одобрения или отклонения.
    При нажатии на кнопку обрабатывается POST-запрос, обновляется статус заявки,
    а при одобрении происходит списание товара со склада.
    """
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'supplier':
        return redirect(url_for('login'))
    supplier_id = user['id']
    message = None

    if request.method == 'POST':
        order_id = request.form.get('order_id')
        action = request.form.get('action')
        if not order_id or not action:
            message = "Некорректные данные заявки."
        else:
            if action == 'approve':
                # Сначала изменяем статус заявки на approved
                if update_order_status(order_id, 'approved'):
                    # Получаем данные заявки, чтобы списать товар
                    # Допустим, для упрощения, получаем card_id через orders и списываем desired_qty
                    conn = sqlite3.connect('Main.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT card_id, desired_qty FROM orders WHERE id=?', (order_id,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        card_id, desired_qty = result[0], result[1]
                        # Пытаемся списать товар
                        if update_card_quantity(card_id, -desired_qty):
                            message = f"Заявка #{order_id} успешно одобрена, товар списан."
                        else:
                            # Если товара не хватает, откатываем статус заявки
                            update_order_status(order_id, 'pending')
                            message = f"Недостаточно товара для заявки #{order_id}."
                    else:
                        message = "Заявка не найдена."
                else:
                    message = f"Ошибка при обновлении заявки #{order_id}."
            elif action == 'reject':
                if update_order_status(order_id, 'rejected'):
                    message = f"Заявка #{order_id} отклонена."
                else:
                    message = f"Ошибка при отклонении заявки #{order_id}."
            else:
                message = "Неизвестное действие."

    orders = get_orders_by_supplier(supplier_id)
    return render_template('supplierOrders.html', orders=orders, message=message, username=username)
# <<< НОВЫЙ ФУНКЦИОНАЛ <<<

# -----------------------------------------------------------------------------
# 7. Маршруты: LOGIN, SUPPLIER, BUSINESS, и т.д.
# (Остальные маршруты ниже не изменялись)
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

@app.route('/supplier', methods=['GET', 'POST'])
def supplier_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'supplier':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        if name and quantity and price:
            save_card_to_db(name, quantity, float(price), user['id'])
            return redirect(url_for('supplier_page'))

    cards = get_cards_by_supplier(user['id'])
    return render_template('mainSupply.html', cards=cards, username=username)

@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    # Рендерим mainBusiness.html (см. ниже)
    return render_template('mainBusiness.html', username=username)

@app.route('/api/cards', methods=['GET'])
def api_cards():
    try:
        cards = get_all_cards()
        return jsonify(cards)
    except Exception as e:
        print("Ошибка /api/cards:", e)
        return jsonify({'error': 'Failed to fetch cards'}), 500

@app.route('/supplier/account')
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

@app.route('/business/account')
def business_account():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    
    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'business':
        return redirect(url_for('login'))

    account_data = get_user_account(username)
    if not account_data:
        # Если нет данных, отрендерим mainAccount.html, но передадим ошибку
        return render_template('mainAccount.html', error="Account data not found.", username=username)

    # Если данные получены, отрендерим тот же шаблон (или другой, если хотите)
    return render_template(
        'mainAccount.html',  # Или 'mainAccountBusiness.html'
        username=username,
        legal_name=account_data[0],
        inn=account_data[1],
        kpp=account_data[2],
        ogrn=account_data[3],
        legal_address=account_data[4],
        contact=account_data[5]
    )

# -----------------------------------------------------------------------------
# 8. Маршрут BUY: покупка товара
# -----------------------------------------------------------------------------
@app.route('/buy/<int:card_id>', methods=['GET','POST'])
def buy_item(card_id):
    """
    При GET – рендерим purchase.html с данными о товаре.
    При POST – обрабатываем покупку (количество) и создаём заявку на покупку.
    """
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user:
        return redirect(url_for('login'))
    # По желанию можно проверить, что user['role'] == 'business' (или другая логика)

    card = get_card_by_id(card_id)
    if not card:
        return "<h1>Товар не найден</h1>"

    if request.method == 'POST':
        desired_qty = request.form.get('desired_qty')
        if not desired_qty:
            return render_template('purchase.html', card=card, error="Укажите количество")

        try:
            desired_qty = int(desired_qty)
        except:
            return render_template('purchase.html', card=card, error="Неверное количество")

        if desired_qty <= 0:
            return render_template('purchase.html', card=card, error="Количество должно быть > 0")

        if desired_qty > card['quantity']:
            return render_template('purchase.html', card=card,
                                   error="Недостаточно товара на складе!")
        
        # >>> МОДИФИКАЦИЯ: Создаём заявку вместо непосредственного вычитания со склада
        if create_order(card_id, user['id'], desired_qty):
            success_msg = f"Ваша заявка на покупку {desired_qty} шт. товара «{card['name']}» отправлена поставщику."
            return render_template('purchase.html', card=None, success=success_msg)
        else:
            return render_template('purchase.html', card=card, error="Ошибка при создании заявки.")
        # <<< МОДИФИКАЦИЯ

    # Если GET
    return render_template('purchase.html', card=card)

# -----------------------------------------------------------------------------
# 9. Регистрация (заявка)
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
        # ... Сохраняем в pending_users, возвращаем pending_id ...
        return render_template('Registration.html', success_message="Ожидайте подтверждения (пример)")
    return render_template('Registration.html')

# -----------------------------------------------------------------------------
# 10. Страница /security-service (Управление заявками и пользователями)
# -----------------------------------------------------------------------------
@app.route('/security-service', methods=['GET', 'POST'])
def security_service():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'security':
        return redirect(url_for('login'))

    message = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve_pending':
            pending_id = request.form.get('pending_id')
            if pending_id:
                update_pending_status(pending_id, 'approved')
                ok, msg = move_pending_to_users(pending_id)
                if ok:
                    message = f"Заявка #{pending_id} одобрена и пользователь добавлен."
                else:
                    message = f"Ошибка: {msg}"

        elif action == 'reject_pending':
            pending_id = request.form.get('pending_id')
            if pending_id:
                ok = update_pending_status(pending_id, 'rejected')
                if ok:
                    message = f"Заявка #{pending_id} отклонена."
                else:
                    message = "Ошибка при отклонении заявки."

        elif action == 'add_user':
            new_username = request.form.get('username')
            new_password = request.form.get('password')
            new_role = request.form.get('role')
            new_legal_name = request.form.get('legal_name')
            new_inn = request.form.get('inn')
            new_kpp = request.form.get('kpp')
            new_ogrn = request.form.get('ogrn')
            new_legal_address = request.form.get('legal_address')
            new_contact = request.form.get('contact')

            ok = add_user(new_username, new_password, new_role, new_legal_name, new_inn, new_kpp, new_ogrn, new_legal_address, new_contact)
            if ok:
                message = f"Пользователь {new_username} добавлен."
            else:
                message = "Ошибка при добавлении пользователя."

        elif action == 'update_user':
            user_id = request.form.get('user_id')
            new_username = request.form.get('username')
            new_password = request.form.get('password')
            new_role = request.form.get('role')
            new_legal_name = request.form.get('legal_name')
            new_inn = request.form.get('inn')
            new_kpp = request.form.get('kpp')
            new_ogrn = request.form.get('ogrn')
            new_legal_address = request.form.get('legal_address')
            new_contact = request.form.get('contact')

            ok = update_user(user_id, new_username, new_password, new_role, new_legal_name, new_inn, new_kpp, new_ogrn, new_legal_address, new_contact)
            if ok:
                message = f"Пользователь #{user_id} обновлён."
            else:
                message = "Ошибка при обновлении пользователя."

        elif action == 'delete_user':
            user_id = request.form.get('user_id')
            ok = delete_user(user_id)
            if ok:
                message = f"Пользователь #{user_id} удалён."
            else:
                message = "Ошибка при удалении пользователя."

    pending_list = get_all_pending()
    user_list = get_all_users()

    return render_template('SecurityService.html',
                           pending_list=pending_list,
                           user_list=user_list,
                           message=message)

# -----------------------------------------------------------------------------
# 11. Запуск
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)