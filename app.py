from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
import sqlite3

app = Flask(__name__)

# ----------------- 1. Работа с заявками на покупку ------------------

def create_order(card_id, buyer_id, quantity):
    """Создание заявки на покупку."""
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (card_id, buyer_id, quantity, status)
            VALUES (?, ?, ?, ?)
        ''', (card_id, buyer_id, quantity, 'pending'))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка create_order:", e)
        return False

def get_orders_by_supplier(supplier_id):
    """Получение заявок, относящихся к товарам поставщика."""
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, c.name, u.username, o.quantity, o.status
            FROM orders o
            JOIN cards c ON o.card_id = c.id
            JOIN users u ON o.buyer_id = u.id
            WHERE c.supplier_id = ?
        ''', (supplier_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': row[0], 'product_name': row[1], 'buyer': row[2], 'quantity': row[3], 'status': row[4]} for row in rows]
    except Exception as e:
        print("Ошибка get_orders_by_supplier:", e)
        return []

def update_order_status(order_id, new_status):
    """Обновление статуса заявки."""
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка update_order_status:", e)
        return False

# ----------------- 2. Маршруты для заявок поставщика ------------------

@app.route('/supplier/orders', methods=['GET', 'POST'])
def supplier_orders():
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

        if action == 'approve':
            if update_order_status(order_id, 'approved'):
                message = f"Заявка #{order_id} принята."
            else:
                message = f"Ошибка при принятии заявки #{order_id}."
        elif action == 'reject':
            if update_order_status(order_id, 'rejected'):
                message = f"Заявка #{order_id} отклонена."
            else:
                message = f"Ошибка при отклонении заявки #{order_id}."

    orders = get_orders_by_supplier(supplier_id)
    return render_template('supplierOrders.html', orders=orders, message=message, username=username)

# ----------------- 3. Обновление маршрута покупки ------------------

@app.route('/buy/<int:card_id>', methods=['GET', 'POST'])
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
        except ValueError:
            return render_template('purchase.html', card=card, error="Неверное количество")

        if desired_qty <= 0:
            return render_template('purchase.html', card=card, error="Количество должно быть больше 0")

        if desired_qty > card['quantity']:
            return render_template('purchase.html', card=card, error="Недостаточно товара на складе!")

        # Создаем заявку вместо вычитания количества
        if create_order(card_id, user['id'], desired_qty):
            return render_template('purchase.html', success=f"Заявка на покупку {desired_qty} шт. товара «{card['name']}» отправлена.", card=None)
        else:
            return render_template('purchase.html', card=card, error="Ошибка при создании заявки.")

    return render_template('purchase.html', card=card)

# -----------------------------------------------------------------------------
# 4. Запуск сервера
# -----------------------------------------------------------------------------

# НОВЫЙ ФУНКЦИОНАЛ
def check_user(username, password):
    """
    Пример функции проверки пользователя (заглушка).
    Возвращает структуру типа:
    {
      'id': int,
      'username': str,
      'role': str,  # 'supplier' или 'buyer'
      'password': str
    }
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, password
            FROM users
            WHERE username = ? AND password = ?
        ''', (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'role': row[2],
                'password': row[3]
            }
        return None
    except Exception as e:
        print("Ошибка check_user:", e)
        return None

def get_card_by_id(card_id):
    """
    Пример функции получения карточки товара (заглушка).
    Возвращает dict { 'id':..., 'name':..., 'quantity':..., 'supplier_id':... }
    или None, если не найден.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, quantity, supplier_id
            FROM cards
            WHERE id = ?
        ''', (card_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'quantity': row[2],
                'supplier_id': row[3]
            }
        return None
    except Exception as e:
        print("Ошибка get_card_by_id:", e)
        return None

def get_order_by_id(order_id):
    """
    Получить заявку по её ID, чтобы узнать card_id и нужное количество.
    Возвращает словарь { 'card_id':..., 'quantity':..., 'buyer_id':..., 'status':... }
    или None, если не найдено.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT card_id, quantity, buyer_id, status
            FROM orders
            WHERE id = ?
        ''', (order_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'card_id': row[0],
                'quantity': row[1],
                'buyer_id': row[2],
                'status': row[3]
            }
        return None
    except Exception as e:
        print("Ошибка get_order_by_id:", e)
        return None

def update_card_quantity(card_id, delta):
    """
    Уменьшить или увеличить (delta может быть отрицательным) количество товара.
    Возвращает True, если операция прошла успешно, False — если нет.
    """
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM cards WHERE id = ?', (card_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        current_qty = row[0]
        new_qty = current_qty + delta
        if new_qty < 0:
            conn.close()
            return False
        
        cursor.execute('UPDATE cards SET quantity = ? WHERE id = ?', (new_qty, card_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Ошибка update_card_quantity:", e)
        return False

@app.route('/supplier/orders/extended', methods=['GET', 'POST'])
def supplier_orders_extended():
    """
    Расширенный маршрут для заявок поставщика:
    - При approve: ставим статус 'approved', затем уменьшаем товар на складе;
      если товара не хватило, откатываем статус обратно.
    - При reject: ставим статус 'rejected'.
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
            message = "Некорректные данные для заявки."
        else:
            if action == 'approve':
                if update_order_status(order_id, 'approved'):
                    order_info = get_order_by_id(order_id)
                    if order_info:
                        qty = order_info['quantity']
                        card_id = order_info['card_id']
                        if not update_card_quantity(card_id, -qty):
                            update_order_status(order_id, 'pending')
                            message = f"Недостаточно товара для заявки #{order_id}."
                        else:
                            message = f"Заявка #{order_id} успешно одобрена."
                    else:
                        message = f"Заявка #{order_id} не найдена."
                else:
                    message = f"Ошибка при принятии заявки #{order_id}."
            elif action == 'reject':
                if update_order_status(order_id, 'rejected'):
                    message = f"Заявка #{order_id} отклонена."
                else:
                    message = f"Ошибка при отклонении заявки #{order_id}."
            else:
                message = f"Неизвестное действие: {action}"

    orders = get_orders_by_supplier(supplier_id)
    return render_template('supplierOrders.html', orders=orders, message=message, username=username)

@app.route('/supplier/products', methods=['GET'])
def supplier_products():
    """
    Пример нового маршрута для просмотра списка товаров поставщика.
    """
    username = request.cookies.get('username')
    if not username:
        return redirect(url_for('login'))

    user = check_user(username, request.cookies.get('password'))
    if not user or user['role'] != 'supplier':
        return redirect(url_for('login'))

    supplier_id = user['id']
    products = []
    try:
        conn = sqlite3.connect('Main.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, quantity
            FROM cards
            WHERE supplier_id = ?
        ''', (supplier_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            products.append({
                'id': row[0],
                'name': row[1],
                'quantity': row[2]
            })
    except Exception as e:
        print("Ошибка при получении списка товаров:", e)

    return render_template('supplierProducts.html', products=products, username=username)

if __name__ == '__main__':
    app.run(debug=True)