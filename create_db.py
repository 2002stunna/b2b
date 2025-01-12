import sqlite3

conn = sqlite3.connect('Main.db')
cursor = conn.cursor()

# ------------------- Таблица users -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    LegalName TEXT,
    INN TEXT,
    KPP TEXT,
    OGRN TEXT,
    LegalAddress TEXT,
    Contact TEXT
)
''')

# ------------------- Таблица cards -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    supplier_id INTEGER NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES users(id)
)
''')

# ------------------- Таблица для "заявок" (если используете) -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS pending_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    LegalName TEXT,
    INN TEXT,
    KPP TEXT,
    OGRN TEXT,
    LegalAddress TEXT,
    Contact TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
)
''')

# ------------------- Таблица orders (заявок покупателей) -------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    desired_qty INTEGER NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (buyer_id) REFERENCES users(id)
)
''')

# ------------------- Тестовые пользователи -------------------
cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('vova', '1234', 'business', 'ООО Вова', '1234567890', '987654321', '1122334455667', 'г. Москва, ул. Вова, д. 1', 'vova@mail.com'))

cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('gosha', '1234', 'supplier', 'ООО Гоша', '0987654321', '123456789', '2233445566778', 'г. Санкт-Петербург, ул. Гоша, д. 2', 'gosha@mail.com'))

cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('igor', '1234', 'business', 'ООО Игорь', '1122334455', '556677889', '3344556677889', 'г. Казань, ул. Игорь, д. 3', 'igor@mail.com'))

cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('katya', '1234', 'supplier', 'ООО Катя', '4455667788', '778899001', '4455667788990', 'г. Новосибирск, ул. Катя, д. 4', 'katya@mail.com'))

# Сотрудник безопасности
cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role, LegalName, INN, KPP, OGRN, LegalAddress, Contact)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('security_user', '1234', 'security', 'ООО Безопасность', '1122334455', '998877665', '3344556677889', 'г. Москва, ул. Безопасности, д. 1', 'sec@mail.com'))

# ------------------- Пример карточек -------------------
cursor.execute('INSERT OR IGNORE INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
               ('Product A', 10, 99.99, 2))
cursor.execute('INSERT OR IGNORE INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
               ('Product B', 20, 49.99, 4))
cursor.execute('INSERT OR IGNORE INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
               ('Product C', 30, 19.99, 2))

conn.commit()
conn.close()

print("База данных инициализирована.")