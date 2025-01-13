import os
import json
import base64
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_PATH = "Main.db"

# ----------------- 1. Проверка пользователя ------------------
def check_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            # row = (id, username, password, role, LegalName, ...)
            return {'id': row[0], 'username': row[1], 'role': row[3]}
        return None
    except Exception as e:
        print("[check_user] Ошибка:", e)
        return None

# ----------------- 2. Pending users (заявки) операции ------------------
def get_all_pending():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pending_users')
        rows = cursor.fetchall()
        conn.close()
        return rows  # (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact, status)
    except Exception as e:
        print("[get_all_pending] Ошибка:", e)
        return []

def update_pending_status(pending_id, new_status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE pending_users SET status=? WHERE id=?', (new_status, pending_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[update_pending_status] Ошибка:", e)
        return False

def move_pending_to_users(pending_id):
    """Перенести запись из pending_users в users (по заявке)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pending_users WHERE id=?', (pending_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Заявка не найдена"
        cursor.execute('''
            INSERT INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
        conn.commit()
        conn.close()
        return True, "Пользователь добавлен"
    except Exception as e:
        print("[move_pending_to_users] Ошибка:", e)
        return False, str(e)

# ----------------- 3. Users (основная таблица) операции ------------------
def get_all_users():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        rows = cursor.fetchall()
        conn.close()
        return rows  # (id, username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
    except Exception as e:
        print("[get_all_users] Ошибка:", e)
        return []

def add_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[add_user] Ошибка:", e)
        return False

def update_user(user_id, username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    try:
        conn = sqlite3.connect(DB_PATH)
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
        print("[update_user] Ошибка:", e)
        return False

def delete_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[delete_user] Ошибка:", e)
        return False

# ----------------- 4. Работа с карточками ------------------
def get_all_cards():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards')
        cards = cursor.fetchall()
        conn.close()
        return [{'id': c[0], 'name': c[1], 'quantity': c[2], 'price': c[3]} for c in cards]
    except Exception as e:
        print("[get_all_cards] Ошибка:", e)
        return []

def get_cards_by_supplier(supplier_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE supplier_id=?', (supplier_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'name': r[1], 'quantity': r[2], 'price': r[3]} for r in rows]
    except Exception as e:
        print("[get_cards_by_supplier] Ошибка:", e)
        return []

def save_card_to_db(name, quantity, price, supplier_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)',
                       (name, quantity, price, supplier_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print("[save_card_to_db] Ошибка:", e)

# ----------------- 5. Получение информации об аккаунте ------------------
def get_user_account(username):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT LegalName, INN, KPP, OGRN, LegalAddress, Contact FROM users WHERE username=?', (username,))
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        print("[get_user_account] Ошибка:", e)
        return None

# ----------------- 6. Получение карточки по id ------------------
def get_card_by_id(card_id):
    try:
        conn = sqlite3.connect(DB_PATH)
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
        print("[get_card_by_id] Ошибка:", e)
        return None

# ----------------- Работа с заказами ------------------
def create_order(card_id, buyer_id, desired_qty):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (card_id, buyer_id, desired_qty, status)
            VALUES (?, ?, ?, ?)
        ''', (card_id, buyer_id, desired_qty, 'approved'))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[create_order] Ошибка:", e)
        return False

def get_orders_by_supplier(supplier_id):
    try:
        conn = sqlite3.connect(DB_PATH)
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
        return [{'order_id': r[0], 'buyer': r[1], 'desired_qty': r[2], 'status': r[3], 'product_name': r[4]} for r in rows]
    except Exception as e:
        print("[get_orders_by_supplier] Ошибка:", e)
        return []

def update_order_status(order_id, new_status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status=? WHERE id=?', (new_status, order_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("[update_order_status] Ошибка:", e)
        return False

def update_card_quantity(card_id, delta):
    try:
        conn = sqlite3.connect(DB_PATH)
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
        print("[update_card_quantity] Ошибка:", e)
        return False

def get_orders_by_buyer(buyer_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, c.name, o.desired_qty, o.status
            FROM orders o
            JOIN cards c ON o.card_id = c.id
            WHERE o.buyer_id = ?
        ''', (buyer_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{'order_id': r[0], 'product_name': r[1], 'desired_qty': r[2], 'status': r[3]} for r in rows]
    except Exception as e:
        print("[get_orders_by_buyer] Ошибка:", e)
        return []

# ----------------------- Маршруты аутентификации и основные -----------------------

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
    orders = get_orders_by_supplier(user['id'])
    return render_template('mainSupply.html', cards=cards, orders=orders, username=username)

@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'business':
        return redirect(url_for('login'))
    orders = get_orders_by_buyer(user['id'])
    return render_template('mainBusiness.html', username=username, orders=orders)

@app.route('/api/cards', methods=['GET'])
def api_cards():
    try:
        cards = get_all_cards()
        return jsonify(cards)
    except Exception as e:
        print("[api/cards] Ошибка:", e)
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
    return render_template('mainAccount.html',
                           username=username,
                           legal_name=account_data[0],
                           inn=account_data[1],
                           kpp=account_data[2],
                           ogrn=account_data[3],
                           legal_address=account_data[4],
                           contact=account_data[5])

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
        return render_template('mainAccount.html', error="Account data not found.", username=username)
    return render_template('mainAccount.html',
                           username=username,
                           legal_name=account_data[0],
                           inn=account_data[1],
                           kpp=account_data[2],
                           ogrn=account_data[3],
                           legal_address=account_data[4],
                           contact=account_data[5])

@app.route('/buy/<int:card_id>', methods=['GET','POST'])
def buy_item(card_id):
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user:
        return redirect(url_for('login'))
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
            return render_template('purchase.html', card=card, error="Недостаточно товара на складе!")
        if create_order(card_id, user['id'], desired_qty):
            success_msg = f"Ваша заявка на покупку {desired_qty} шт. товара «{card['name']}» отправлена поставщику."
            return render_template('purchase.html', card=None, success=success_msg)
        else:
            return render_template('purchase.html', card=card, error="Ошибка при создании заявки.")
    return render_template('purchase.html', card=card)

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
        # Здесь можно сохранить заявку в pending_users
        return render_template('Registration.html', success_message="Ожидайте подтверждения (пример)")
    return render_template('Registration.html')

# ----------------- FACE ID REGISTRATION / Вход -----------------

# Страница настроек Face ID (для покупателя)
@app.route('/faceid-settings', methods=['GET'])
def faceid_settings():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))
    user = check_user(username, request.cookies.get('password'))
    if not user:
        return redirect(url_for('login'))
    return render_template('faceid_settings.html', username=username, user_id=user['id'], display_name=user['username'])

# Эндпоинт для начала регистрации Face ID
@app.route('/register/begin', methods=['POST'])
def register_begin():
    try:
        data = request.get_json()
        print("[FaceID Begin] Получены данные:", data)
        user_id = data.get('user_id')
        username = data.get('username')
        display_name = data.get('display_name')
        if not all([user_id, username, display_name]):
            print("[FaceID Begin] Недостаточно данных для начала регистрации.")
            return jsonify({"status": "error", "message": "Недостаточно данных."}), 400
        challenge = os.urandom(32).hex()
        print("[FaceID Begin] Сгенерированный challenge:", challenge)
        options = {
            "publicKey": {
                "challenge": challenge,
                "rp": {"name": "Demo RP", "id": request.host.split(':')[0]},
                "user": {
                    "id": str(user_id),
                    "name": username,
                    "displayName": display_name
                },
                "pubKeyCredParams": [{"type": "public-key", "alg": -7}],
                "timeout": 60000,
                "attestation": "direct"
            }
        }
        print("[FaceID Begin] Отправляем опции для регистрации:", options)
        return jsonify(options)
    except Exception as e:
        print("[FaceID Begin] Ошибка при начале регистрации:", e)
        return jsonify({"status": "error", "message": "Ошибка при начале регистрации."}), 500

# Эндпоинт для завершения регистрации Face ID
@app.route('/register/complete', methods=['POST'])
def register_complete():
    try:
        data = request.get_json()
        print("[FaceID Complete] Получены данные:", data)
        user_id = data.get('user_id')
        clientDataJSON = data.get('clientDataJSON')
        attestationObject = data.get('attestationObject')
        if not all([user_id, clientDataJSON, attestationObject]):
            print("[FaceID Complete] Недостаточно данных для завершения регистрации.")
            return jsonify({"status": "error", "message": "Недостаточно данных."}), 400
        # Здесь должна выполняться валидация attestation; используем заглушку:
        credential_id = f"credential_{user_id}"
        public_key = "dummy_public_key"
        rp_id = request.host.split(':')[0]
        user_handle = str(user_id)
        print("[FaceID Complete] Сохранение данных в БД для user_id", user_id)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO face_id_credentials (user_id, credential_id, public_key, rp_id, user_handle)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, credential_id, public_key, rp_id, user_handle))
            conn.commit()
            conn.close()
            print("[FaceID Complete] Данные успешно сохранены в базе.")
            return jsonify({"status": "ok", "message": "Face ID registration complete."})
        except Exception as db_e:
            print("[FaceID Complete] Ошибка при сохранении в БД:", db_e)
            return jsonify({"status": "error", "message": "Ошибка сохранения в базе."}), 500
    except Exception as e:
        print("[FaceID Complete] Общая ошибка регистрации:", e)
        return jsonify({"status": "error", "message": "Ошибка при завершении регистрации."}), 500

# Эндпоинт для получения опций входа по Face ID
@app.route('/auth/face-id/options', methods=['GET'])
def faceid_login_options():
    try:
        challenge = os.urandom(32).hex()
        print("[FaceID Login Options] Сгенерированный challenge:", challenge)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT credential_id FROM face_id_credentials')
            rows = cursor.fetchall()
            conn.close()
            allowed = [{"type": "public-key", "id": row[0]} for row in rows]
            print("[FaceID Login Options] Разрешённые credential_id:", allowed)
        except Exception as db_e:
            print("[FaceID Login Options] Ошибка при получении данных из БД:", db_e)
            allowed = []
        options = {
            "challenge": challenge,
            "allowCredentials": allowed,
            "timeout": 60000,
            "rpId": request.host.split(':')[0]
        }
        print("[FaceID Login Options] Отправляем опции входа:", options)
        return jsonify(options)
    except Exception as e:
        print("[FaceID Login Options] Общая ошибка получения опций:", e)
        return jsonify({"status": "error", "message": "Ошибка при получении опций входа."}), 500

# Эндпоинт для верификации входа по Face ID
@app.route('/auth/face-id/verify', methods=['POST'])
def faceid_verify():
    try:
        data = request.get_json()
        print("[FaceID Verify] Получены данные:", data)
        credential_id = data.get('id')
        if not credential_id:
            print("[FaceID Verify] Не передан credential_id.")
            return jsonify({"status": "error", "message": "No credential id provided."}), 400
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM face_id_credentials WHERE credential_id=?', (credential_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                user_id = row[0]
                print("[FaceID Verify] Найден user_id:", user_id)
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT username, password, role FROM users WHERE id=?', (user_id,))
                user_row = cursor.fetchone()
                conn.close()
                if user_row:
                    username = user_row[0]
                    password = user_row[1]
                    print("[FaceID Verify] Успешная верификация. Авторизуем пользователя:", username)
                    response = make_response(jsonify({"status": "ok"}))
                    response.set_cookie("username", username)
                    response.set_cookie("password", password)
                    return response
                else:
                    print("[FaceID Verify] Пользователь не найден по user_id:", user_id)
            else:
                print("[FaceID Verify] Credential id не найден в базе:", credential_id)
        except Exception as db_e:
            print("[FaceID Verify] Ошибка при обращении к БД:", db_e)
        return jsonify({"status": "error", "message": "Verification failed."}), 400
    except Exception as e:
        print("[FaceID Verify] Общая ошибка верификации:", e)
        return jsonify({"status": "error", "message": "Ошибка при верификации."}), 500

# ----------------------- Дополнительные маршруты -----------------------

@app.route('/webauthn-login', methods=['GET'])
def webauthn_login():
    username = "faceid_user"  # Заглушка для демонстрации
    response = make_response(redirect(url_for('business_page')))
    response.set_cookie('username', username)
    response.set_cookie('password', '')
    return response

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

if __name__ == '__main__':
    app.run(debug=True)