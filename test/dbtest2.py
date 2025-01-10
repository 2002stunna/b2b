'''import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM cards")
cards = cursor.fetchall()

print("Данные в таблице cards:")
for card in cards:
    print(card)

conn.close()'''

import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM cards')
cards = cursor.fetchall()

print("Данные в таблице cards:")
for card in cards:
    print(card)

conn.close()