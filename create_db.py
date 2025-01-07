import sqlite3

# Подключение к базе данных (если файла нет, он создастся автоматически)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создание таблицы пользователей с атрибутом role
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL -- Роль пользователя: 'supplier' или 'business'
)
''')

# Добавление тестовых пользователей
cursor.execute('''
INSERT INTO users (username, password, role)
VALUES (?, ?, ?)
''', ('vova', '1234', 'business'))  # Добавляем пользователя с ролью 'business'

cursor.execute('''
INSERT INTO users (username, password, role)
VALUES (?, ?, ?)
''', ('gosha', '1234', 'supplier'))  # Добавляем пользователя с ролью 'supplier'

conn.commit()
conn.close()

print("База данных создана, пользователи добавлены.")