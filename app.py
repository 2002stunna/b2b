import sqlite3
from flask import Flask, request, render_template, redirect, url_for, make_response

app = Flask(__name__)

# ---------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------------

def check_user(username, password):
    """
    Проверка пользователя в базе данных (пример).
    Возвращает словарь {id, username, role} или None, если не найден.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            # Допустим, структура таблицы users:
            # (id, username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact)
            return {'id': user[0], 'username': user[1], 'role': user[3]}
        return None
    except Exception as e:
        print(f"Ошибка в check_user: {e}")
        return None


def save_user_to_db(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
    """
    Сохранение нового пользователя в базу данных.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        # Пример структуры таблицы users (id автогенерируется):
        # CREATE TABLE users (
        #   id INTEGER PRIMARY KEY AUTOINCREMENT,
        #   username TEXT UNIQUE,
        #   password TEXT,
        #   role TEXT,
        #   legal_name TEXT,
        #   inn TEXT,
        #   kpp TEXT,
        #   ogrn TEXT,
        #   legal_address TEXT,
        #   contact TEXT
        # );
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


def get_cards_by_supplier(supplier_id):
    """
    Возвращает список карточек (товаров) по ID поставщика.
    Структура таблицы cards: (id, name, quantity, price, supplier_id)
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE supplier_id = ?', (supplier_id,))
        cards = cursor.fetchall()
        conn.close()
        return [
            {
                'id': card[0],
                'name': card[1],
                'quantity': card[2],
                'price': card[3]
            } 
            for card in cards
        ]
    except Exception as e:
        print(f"Ошибка при получении карточек поставщика: {e}")
        return []


def save_card_to_db(name, quantity, price, supplier_id):
    """
    Сохранение карточки товара в базе данных.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)',
                       (name, quantity, price, supplier_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при сохранении карточки: {e}")


# ---------------------- МАРШРУТЫ ----------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Пример страницы логина (не менялась).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Both fields are required!", username=None)

        user = check_user(username, password)
        if user:
            response = make_response(
                redirect(
                    url_for('supplier_page') if user['role'] == 'supplier' else url_for('security_service')
                )
            )
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response
        else:
            return render_template('login.html', error="Invalid username or password", username=None)

    return render_template('login.html', username=None)


@app.route('/register', methods=['GET'])
def register():
    """
    Просто рендерит форму для регистрации.
    POST-логика здесь не нужна, так как форма отправляется напрямую на /security-service.
    """
    return render_template('Registration.html')


@app.route('/security-service', methods=['GET', 'POST'])
def security_service():
    """
    Получаем данные формы из Registration.html (POST)
    и показываем их на странице SecurityService.html,
    чтобы оператор мог принять или отклонить.
    """
    if request.method == 'POST':
        # Данные, которые пришли из формы на Registration.html
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        legal_name = request.form.get('legal_name')
        inn = request.form.get('inn')
        kpp = request.form.get('kpp')
        ogrn = request.form.get('ogrn')
        legal_address = request.form.get('legal_address')
        contact = request.form.get('contact')

        # Отображаем их на SecurityService.html для проверки оператором
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
    else:
        # GET-запрос: покажем страницу без данных или сообщение
        return render_template('SecurityService.html', message="Нет данных для проверки.")


@app.route('/approve-user', methods=['POST'])
def approve_user():
    """
    Оператор нажал "Принять" на странице SecurityService.html.
    Данные сохраняются в БД.
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

    if save_user_to_db(username, password, role, legal_name, inn, kpp, ogrn, legal_address, contact):
        message = "Пользователь успешно добавлен в базу!"
    else:
        message = "Ошибка при добавлении пользователя в базу."

    return render_template('SecurityService.html', message=message)


@app.route('/reject-user', methods=['POST'])
def reject_user():
    """
    Оператор нажал "Отклонить" на странице SecurityService.html.
    Ничего не сохраняем, просто показываем результат.
    """
    message = "Регистрация пользователя отклонена."
    return render_template('SecurityService.html', message=message)


@app.route('/supplier', methods=['GET', 'POST'])
def supplier_page():
    """
    Пример страницы для поставщика (не менялась).
    """
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


if __name__ == '__main__':
    app.run(debug=True)