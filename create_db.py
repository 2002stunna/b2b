import sqlite3

# Подключение к базе данных (если файла нет, он создастся автоматически)
conn = sqlite3.connect('Main.db')
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

# Создание таблицы карточек с привязкой к поставщику
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

# Добавление тестовых пользователей
cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role)
VALUES (?, ?, ?)
''', ('vova', '1234', 'business'))

cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role)
VALUES (?, ?, ?)
''', ('gosha', '1234', 'supplier'))

cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role)
VALUES (?, ?, ?)
''', ('igor', '1234', 'business'))

cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role)
VALUES (?, ?, ?)
''', ('katya', '1234', 'supplier'))

# Добавляем тестовые карточки
cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
               ('Product A', 10, 99.99, 1))
cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
               ('Product B', 20, 49.99, 2))
cursor.execute('INSERT INTO cards (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)', 
               ('Product C', 30, 19.99, 1))

conn.commit()
conn.close()

print("База данных инициализирована.")