import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


def get_db():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'spendly.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    cursor.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@spendly.com', generate_password_hash('demo123'))
    )
    user_id = cursor.lastrowid

    expenses = [
        (user_id, 12.50, 'Food', '2026-04-01', 'Lunch at cafe'),
        (user_id, 45.00, 'Transport', '2026-04-03', 'Uber rides'),
        (user_id, 120.00, 'Bills', '2026-04-05', 'Electricity bill'),
        (user_id, 30.00, 'Health', '2026-04-08', 'Pharmacy'),
        (user_id, 60.00, 'Entertainment', '2026-04-10', 'Movie tickets'),
        (user_id, 85.00, 'Shopping', '2026-04-14', 'Clothing'),
        (user_id, 15.75, 'Food', '2026-04-17', 'Grocery run'),
        (user_id, 20.00, 'Other', '2026-04-20', 'Miscellaneous expense'),
    ]

    cursor.executemany(
        'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
        expenses
    )

    conn.commit()
    conn.close()


def create_user(name, email, password):
    email = email.lower()
    password_hash = generate_password_hash(password)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            (name, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    email = email.lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_expenses(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC',
        (user_id,)
    )
    expenses = cursor.fetchall()
    conn.close()
    return expenses


def get_user_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT SUM(amount) FROM expenses WHERE user_id = ?',
        (user_id,)
    )
    total_spent = cursor.fetchone()[0] or 0.0

    cursor.execute(
        'SELECT COUNT(*) FROM expenses WHERE user_id = ?',
        (user_id,)
    )
    transaction_count = cursor.fetchone()[0] or 0

    cursor.execute(
        'SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1',
        (user_id,)
    )
    top_result = cursor.fetchone()
    top_category = top_result[0] if top_result else None

    conn.close()
    return {
        'total_spent': total_spent,
        'transaction_count': transaction_count,
        'top_category': top_category
    }


def get_category_breakdown(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT category, SUM(amount) as total_amount FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total_amount DESC',
        (user_id,)
    )
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories
