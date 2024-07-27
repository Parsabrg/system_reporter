import psutil
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# تنظیمات دیتابیس
DATABASE = 'ram_usage.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ram_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        used REAL,
        free REAL,
        timestamp TEXT
    )
    ''')
    conn.commit()
    conn.close()

# دریافت اطلاعات RAM
def get_ram_info():
    ram = psutil.virtual_memory()
    total = ram.total / (1024 ** 2)  # تبدیل به مگابایت
    used = ram.used / (1024 ** 2)    # تبدیل به مگابایت
    free = ram.free / (1024 ** 2)    # تبدیل به مگابایت
    return total, used, free

# ذخیره اطلاعات RAM در دیتابیس
def save_ram_info():
    while True:
        total, used, free = get_ram_info()
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO ram_usage (total, used, free, timestamp) VALUES (?, ?, ?, ?)
        ''', (total, used, free, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        time.sleep(60)  # هر دقیقه یکبار

# طراحی API برای بازیابی داده‌ها
@app.route('/ram', methods=['GET'])
def get_ram_history():
    n = int(request.args.get('n', 10))  # تعداد رکوردها به عنوان پارامتر query
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT total, used, free, timestamp FROM ram_usage ORDER BY id DESC LIMIT ?', (n,))
    rows = cursor.fetchall()
    conn.close()
    
    history = [{'total': row[0], 'used': row[1], 'free': row[2], 'timestamp': row[3]} for row in rows]
    return jsonify(history)

if __name__ == '__main__':
    init_db()
    
    # اجرای ذخیره‌سازی در یک ترد جداگانه
    save_thread = threading.Thread(target=save_ram_info, daemon=True)
    save_thread.start()
    
    app.run(debug=True)
