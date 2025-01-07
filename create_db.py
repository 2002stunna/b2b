import sqlite3

# Подключение к базе данных (если файла нет, он создастся автоматически)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Добавление тестового пользователя
cursor.execute('''
INSERT INTO users (username, password)
VALUES (?, ?)
''', ('vova', '1234'))  # Пароль в открытом виде только для примера

conn.commit()
conn.close()

print("База данных создана, пользователь добавлен.")