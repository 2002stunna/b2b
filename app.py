from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
import sqlite3

app = Flask(__name__)

# -----------------------------------------------------------------------------
# 1. Проверка пользователя в базе данных (ваш исходный код)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# 2. Получение всех карточек (ваш исходный код)
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
# 3. Получение карточек текущего поставщика (ваш исходный код)
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
# 4. Сохранение карточки (ваш исходный код)
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
# 5. Получение данных аккаунта пользователя (ваш исходный код)
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
# 6. (НОВОЕ) Сохранение нового пользователя в БД
#    Таблица users в Main.db: id, username, password, role, LegalName, INN, ...
# -----------------------------------------------------------------------------
def save_new_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    """
    Сохраняем нового пользователя в БД. Поля должны соответствовать структуре таблицы users.
    """
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
        print(f"Ошибка при сохранении нового пользователя: {e}")
        return False


# -----------------------------------------------------------------------------
# 7. Маршрут LOGIN (ваш исходный код)
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
            # Логика перенаправления в зависимости от user['role']
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
# 8. Маршрут SUPPLIER (ваш исходный код)
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
# 9. Маршрут BUSINESS (ваш исходный код)
# -----------------------------------------------------------------------------
@app.route('/business')
def business_page():
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    return render_template('mainBusiness.html', username=username)


# -----------------------------------------------------------------------------
# 10. API для получения карточек (ваш исходный код)
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
# 11. Страница с данными аккаунта поставщика (ваш исходный код)
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
# 12. (НОВОЕ) Маршрут /register: показ формы регистрации (GET) и отправка (POST)
# -----------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Получаем данные из формы Registration.html
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        legal_name = request.form.get('legal_name')
        inn = request.form.get('inn')
        kpp = request.form.get('kpp')
        ogrn = request.form.get('ogrn')
        legal_address = request.form.get('legal_address')
        contact = request.form.get('contact')

        # Проверяем, что все поля заполнены
        if not all([username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact]):
            return render_template('Registration.html', error="All fields are required!")

        # ВАЖНО: здесь вы можете (при желании) сразу создавать запись в БД
        # например, таблица pending_users или users (со статусом "pending").
        # Но раз вы хотите, чтобы пользователь не шел на SecurityService,
        # просто показываем: "Ожидайте подтверждения заявки".
        
        return render_template('Registration.html', success_message="Ожидайте подтверждения заявки")

    # Если GET-запрос — просто показать страницу регистрации
    return render_template('Registration.html')


# -----------------------------------------------------------------------------
# 13. (НОВОЕ) Маршрут /security-service: можно оставить заглушку или GET-показ
# -----------------------------------------------------------------------------
@app.route('/security-service', methods=['GET', 'POST'])
def security_service():
    # Если нужно, можно отрендерить SecurityService.html без данных
    return render_template('SecurityService.html')


# -----------------------------------------------------------------------------
# 14. (НОВОЕ) "ПРИНЯТЬ" пользователя: сохранение в БД
# -----------------------------------------------------------------------------
@app.route('/approve-user', methods=['POST'])
def approve_user():
    """
    Оператор нажимает "Принять" на SecurityService.html.
    Сохраняем нового пользователя в таблицу users.
    """
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    legal_name = request.form.get('legal_name')
    inn = request.form.get('inn')
    kpp = request.form.get('kpp')
    ogrn = request.form.get('ogrn')
    legal_address = request.form.get('legal_address')
    contact = request.form.get('contact')

    success = save_new_user(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact)

    if success:
        message = "Пользователь успешно добавлен в базу!"
    else:
        message = "Ошибка при добавлении пользователя в базу."

    return render_template('SecurityService.html', message=message)


# -----------------------------------------------------------------------------
# 15. (НОВОЕ) "ОТКЛОНИТЬ" пользователя: не сохраняем, просто сообщение
# -----------------------------------------------------------------------------
@app.route('/reject-user', methods=['POST'])
def reject_user():
    """
    Оператор нажимает "Отклонить" на SecurityService.html.
    Ничего не сохраняем, просто показываем сообщение.
    """
    message = "Регистрация пользователя отклонена."
    return render_template('SecurityService.html', message=message)


# -----------------------------------------------------------------------------
# 16. Точка входа (ваш исходный код)
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)