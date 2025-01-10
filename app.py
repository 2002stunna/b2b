import sqlite3
from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify

app = Flask(__name__)

# -----------------------------------------------------------------------------
# 1. Проверка пользователя в базе данных (не менялась)
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
# 2. Сохранение НОВОГО пользователя в базу (новая функция!)
# -----------------------------------------------------------------------------
def save_user_to_db(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    """
    Сохраняет нового пользователя в таблицу users.
    Предполагается, что структура таблицы users примерно такая:
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            legal_name TEXT,
            inn TEXT,
            kpp TEXT,
            ogrn TEXT,
            legal_address TEXT,
            contact TEXT
        );
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users 
            (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
        return False

# -----------------------------------------------------------------------------
# 3. Получение всех карточек (не менялось)
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
# 4. Получение карточек текущего поставщика (не менялось)
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
# 5. Сохранение карточки в базе данных (не менялось)
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
# 6. Маршрут LOGIN (не менялся; обращаем внимание на редирект supplier_page/business_page)
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
            response = make_response(
                redirect(
                    url_for('supplier_page') if user['role'] == 'supplier' else url_for('business_page')
                )
            )
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response
        else:
            return render_template('login.html', error="Invalid username or password", username=None)

    return render_template('login.html', username=None)

# -----------------------------------------------------------------------------
# 7. Маршрут REGISTER (не менялся; при POST рендерит SecurityService.html с данными)
# -----------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Получение данных из формы
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        legal_name = request.form.get('legal_name')
        inn = request.form.get('inn')
        kpp = request.form.get('kpp')
        ogrn = request.form.get('ogrn')
        legal_address = request.form.get('legal_address')
        contact = request.form.get('contact')

        # Проверка, что все поля заполнены
        if not all([username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact]):
            return render_template('Registration.html', error="All fields are required!")

        # Отправка данных на страницу SecurityService
        return render_template(
            'SecurityService.html',
            username=username,
            password=password,
            role=role,
            legal_name=legal_name,
            inn=inn,
            kpp=kpp,
            ogrn=ogrn,
            legal_address=legal_address,
            contact=contact
        )

    return render_template('Registration.html')

# -----------------------------------------------------------------------------
# 8. Страница SECURITY-SERVICE (добавили методы=['GET', 'POST'])
#    Здесь можно просто рендерить заглушку, если GET.
# -----------------------------------------------------------------------------
@app.route('/security-service', methods=['GET', 'POST'])
def security_service():
    if request.method == 'POST':
        # Если вдруг что-то отправили сюда напрямую POST-ом
        return render_template('SecurityService.html')
    else:
        # GET-запрос: просто показываем пустую (или заглушку)
        return render_template('SecurityService.html')

# -----------------------------------------------------------------------------
# 9. Маршрут "ПРИНЯТЬ" пользователя (новый!)
# -----------------------------------------------------------------------------
@app.route('/approve-user', methods=['POST'])
def approve_user():
    """
    Оператор нажимает "Принять" на странице SecurityService.html.
    Данные пользователя сохраняются в БД.
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

    # Пытаемся сохранить в БД
    success = save_user_to_db(
        username,
        password,
        role,
        legal_name,
        inn,
        kpp,
        ogrn,
        legal_address,
        contact
    )

    if success:
        message = "Пользователь успешно добавлен в базу!"
    else:
        message = "Ошибка при добавлении пользователя в базу."

    return render_template('SecurityService.html', message=message)

# -----------------------------------------------------------------------------
# 10. Маршрут "ОТКЛОНИТЬ" пользователя (новый!)
# -----------------------------------------------------------------------------
@app.route('/reject-user', methods=['POST'])
def reject_user():
    """
    Оператор нажимает "Отклонить" на странице SecurityService.html.
    Ничего не сохраняем, просто выводим сообщение.
    """
    message = "Регистрация пользователя отклонена."
    return render_template('SecurityService.html', message=message)

# -----------------------------------------------------------------------------
# 11. Маршрут SUPPLIER (не менялся)
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
# 12. Страница "business_page" (У ВАС её НЕ БЫЛО, но в логине есть ссылка)
#     Чтобы не было ошибки при else: url_for('business_page'), можно заглушку сделать.
# -----------------------------------------------------------------------------
@app.route('/business_page')
def business_page():
    return "<h1>Business page (заглушка)</h1>"

# -----------------------------------------------------------------------------
# 13. Точка входа
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)