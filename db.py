# db.py
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import config

# Убедимся, что папка для БД есть
Path(config.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


def init_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        """
      CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        label TEXT UNIQUE,
        amount REAL,
        status TEXT,        -- pending или success
        operation_id TEXT,
        created_at TEXT
      )
    """
    )
    cur.execute(
        """
      CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        start_ts INTEGER,
        end_ts   INTEGER,
        reminded INTEGER DEFAULT 0
      )
    """
    )
    # Если в старой БД нет колонки reminded, добавляем её
    cur.execute("PRAGMA table_info(subscriptions)")
    columns = [row[1] for row in cur.fetchall()]
    if "reminded" not in columns:
        cur.execute("ALTER TABLE subscriptions ADD COLUMN reminded INTEGER DEFAULT 0")
    conn.commit()
    conn.close()


def add_payment(user_id: int, label: str, amount: float):
    """Добавляем запись о новом платеже со статусом pending."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO payments (user_id,label,amount,status,created_at) VALUES (?,?,?,?,?)",
        (user_id, label, amount, "pending", datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_pending_payments():
    """Возвращает список всех платежей в статусе pending."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT label, user_id FROM payments WHERE status='pending'")
    rows = cur.fetchall()
    conn.close()
    return [{"label": r[0], "user_id": r[1]} for r in rows]


def mark_payment_success(label: str, operation_id: str):
    """Помечаем платёж как успешный и сохраняем operation_id."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        """
      UPDATE payments 
      SET status='success', operation_id=? 
      WHERE label=?
    """,
        (operation_id, label),
    )
    conn.commit()
    conn.close()


def get_subscription(user_id: int):
    """Возвращает подписку пользователя или None."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT start_ts, end_ts FROM subscriptions WHERE user_id=?", (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"start_ts": row[0], "end_ts": row[1]}


def add_or_update_subscription(user_id: int):
    """Создаем или продлеваем подписку на SUB_DURATION_DAYS."""
    now = int(datetime.now().timestamp())
    sub = get_subscription(user_id)
    if sub and sub["end_ts"] > now:
        start = sub["end_ts"]
    else:
        start = now
    end = start + config.SUB_DURATION_DAYS * 24 * 3600
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute(
        """
      INSERT INTO subscriptions(user_id,start_ts,end_ts)
      VALUES (?,?,?)
      ON CONFLICT(user_id) DO UPDATE SET start_ts=?,end_ts=?
    """,
        (user_id, start, end, start, end),
    )
    conn.commit()
    conn.close()
    return end


def get_expired_subscriptions():
    """Список user_id, у кого end_ts <= сейчас."""
    now = int(datetime.now().timestamp())
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM subscriptions WHERE end_ts<=?", (now,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def remove_subscription(user_id: int):
    conn = sqlite3.connect(config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriptions WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
