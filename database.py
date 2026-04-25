import aiosqlite
import logging
from models import Tx, State


logging.basicConfig(level=logging.INFO, format='[DB LOG] %(message)s')

class DBManager:
    def __init__(self, db_path="xbank.db"):
        self.db_path = db_path
    async def init_db(self):
        """Создание таблиц на старте"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT,
                    address TEXT,
                    balance REAL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    recipient TEXT,
                    amount REAL
                )
            ''')
            await db.commit()
            logging.info("База данных инициализирована.")
    async def load_state(self) -> State:
        """Получение данных при старте программы"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT name, address, balance FROM state WHERE id = 1") as cursor:
                row = await cursor.fetchone()
            if not row:
                logging.info("Данные не найдены. Возвращаем дефолтное состояние.")
                return State(name="New User", address="0x0", balance=0.0)
            name, address, balance = row
            history = []
            async with db.execute("SELECT sender, recipient, amount FROM history") as cursor:
                async for r in cursor:
                    history.append(Tx(sender=r[0], to=r[1], amount=r[2]))
            logging.info(f"Загружен баланс: {balance}, транзакций в истории: {len(history)}")
            return State(name=name, address=address, balance=balance, history=history)
    async def save_all(self, state: State):
        """Сохранение данных перед выходом"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO state (id, name, address, balance) 
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET 
                name=excluded.name, address=excluded.address, balance=excluded.balance
            ''', (state.name, state.address, state.balance))
            await db.execute("DELETE FROM history")
            for tx in state.history:
                await db.execute(
                    "INSERT INTO history (sender, recipient, amount) VALUES (?, ?, ?)",
                    (tx.sender, tx.to, tx.amount)
                )
            await db.commit()
            logging.info(f"Состояние системы сохранено. Финальный баланс: {state.balance}")