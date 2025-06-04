import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
admin_env = os.getenv("ADMINS", "")
ADMINS = [int(admin_id) for admin_id in admin_env.split(",") if admin_id.strip().isdigit()]

DB_PATH = "storage/database.db"

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trackings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            threshold REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
            CREATE TABLE IF NOT EXISTS command_stats (
                command TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        ''')
    conn.commit()
    conn.close()

def get_user(telegram_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user[0]

def add_user(telegram_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (id) VALUES (?)", (telegram_id,))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return get_user(telegram_id)
    finally:
        conn.close()

def add_tracking(user_id: int, game_id: int, game_name: str, threshold: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO trackings (user_id, game_id, game_name, threshold) VALUES (?, ?, ?, ?)",
        (user_id, game_id, game_name, threshold)
    )
    conn.commit()
    conn.close()

def get_trackings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM trackings")
    trackings = c.fetchall()
    conn.close()
    return trackings

def get_user_trackings(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM trackings WHERE user_id = ?", (user_id,))
    trackings = c.fetchall()
    conn.close()
    return trackings


def add_price(game_id: int, price: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO prices (game_id, price) VALUES (?, ?)",
        (game_id, price)
    )
    conn.commit()
    conn.close()

def get_user_trackings_for_keyboard(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, game_name, threshold FROM trackings WHERE user_id = ?", (user_id,))
    trackings = c.fetchall()
    conn.close()
    return [{"id": t[0], "name": t[1], "threshold": t[2]} for t in trackings]

def delete_tracking_by_id(tracking_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM trackings WHERE id = ? AND user_id = ?", (tracking_id, user_id))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

def update_tracking_threshold(tracking_id: int, user_id: int, new_threshold: float) -> bool:
    """
    Обновляет пороговую цену для отслеживания
    :param tracking_id: ID отслеживания
    :param user_id: ID пользователя (для проверки владельца)
    :param new_threshold: Новая пороговая цена
    :return: True если обновление прошло успешно
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE trackings SET threshold = ? WHERE id = ? AND user_id = ?",
        (new_threshold, tracking_id, user_id)
    )
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def increment_command_stat(command: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO command_stats (command, count)
        VALUES (?, 1)
        ON CONFLICT(command) DO UPDATE SET count = count + 1
    ''', (command,))
    conn.commit()
    conn.close()

def get_all_command_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT command, count FROM command_stats ORDER BY count DESC")
    stats = c.fetchall()
    conn.close()
    return stats

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# Инициализация БД при импорте
create_tables()