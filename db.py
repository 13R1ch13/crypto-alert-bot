from pathlib import Path
import aiosqlite
from config import DB_PATH

# Гарантируем, что директория для БД существует
DB_FILE = Path(DB_PATH)
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

INIT_SQL = '''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,              -- 'price' | 'pct'
    op TEXT,                         -- '>=' или '<=' (для price)
    target REAL,                     -- цена (price) или процент (pct)
    window_str TEXT,                 -- окно (15m,30m,1h,4h,1d) для pct
    window_sec INTEGER,              -- окно в секундах (для pct)
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def row_to_dict(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

async def init_db():
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        await db.executescript(INIT_SQL)
        await db.commit()

async def add_price_alert(user_id: int, chat_id: int, symbol: str, op: str, target: float) -> int:
    q = '''INSERT INTO alerts(user_id, chat_id, symbol, type, op, target)
           VALUES(?, ?, ?, 'price', ?, ?)'''
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        cur = await db.execute(q, (user_id, chat_id, symbol, op, target))
        await db.commit()
        return cur.lastrowid

async def add_pct_alert(user_id: int, chat_id: int, symbol: str, percent: float, window_str: str, window_sec: int) -> int:
    q = '''INSERT INTO alerts(user_id, chat_id, symbol, type, target, window_str, window_sec)
           VALUES(?, ?, ?, 'pct', ?, ?, ?)'''
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        cur = await db.execute(q, (user_id, chat_id, symbol, percent, window_str, window_sec))
        await db.commit()
        return cur.lastrowid

async def list_alerts(user_id: int) -> list[dict]:
    q = '''SELECT id, symbol, type, op, target, window_str, active, created_at
          FROM alerts WHERE user_id=? ORDER BY id DESC'''
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        db.row_factory = row_to_dict
        cur = await db.execute(q, (user_id,))
        rows = await cur.fetchall()
        return rows

async def get_active_alerts() -> list[dict]:
    q = '''SELECT * FROM alerts WHERE active=1'''
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        db.row_factory = row_to_dict
        cur = await db.execute(q)
        return await cur.fetchall()

async def deactivate_alert(alert_id: int):
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        await db.execute('UPDATE alerts SET active=0 WHERE id=?', (alert_id,))
        await db.commit()

async def delete_alert(alert_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_FILE.as_posix()) as db:
        cur = await db.execute('DELETE FROM alerts WHERE id=? AND user_id=?', (alert_id, user_id))
        await db.commit()
        return cur.rowcount > 0
