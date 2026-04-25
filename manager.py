import os
import asyncio
import secure_codex
import logging
from models import State, Tx
from database import DBManager

class BankNode:
    DB1 = "storage/vault_a.bin"
    DB2 = "storage/vault_b.bin"

    def __init__(self):
        self.state = None
        self.db = DBManager("storage/xbank.db")
    async def save(self):
        """Кодируем зеркала + сохраняем в SQLite"""
        data_json = self.state.model_dump_json()
        with open(self.DB1, "wb") as f:
            f.write(secure_codex.encoder1(data_json).encode('latin1'))
        with open(self.DB2, "wb") as f:
            f.write(secure_codex.encoder2(data_json).encode('latin1'))
        await self.db.save_all(self.state)
        print("==> Данные синхронизированы: Vault A, Vault B и SQLite")

    async def startup(self):
        """Импорт + Тройная проверка (Vault A vs Vault B vs SQLite)"""
        await self.db.init_db()
        if not os.path.exists(self.DB1) or not os.path.exists(self.DB2):
            print("==> Файлы не найдены. Создаю новый кошелек")
            return False
        with open(self.DB1, "rb") as f:
            d1 = secure_codex.decoder1(f.read().decode('latin1'))
        with open(self.DB2, "rb") as f:
            d2 = secure_codex.decoder2(f.read().decode('latin1'))
        db_state = await self.db.load_state()
        db_data_json = db_state.model_dump_json()
        if d1 != d2 or d1 != db_data_json:
            logging.error("КРИТИЧЕСКАЯ ОШИБКА: Расхождение данных в зеркалах или БД!")
            raise Exception("УСТАНОВЛЕНА ПОПЫТКА ИЗМЕНЕНИЯ БАЛАНСА")
        self.state = State.model_validate_json(d1)
        print(f"==> Проверка пройдена. Баланс подтвержден БД. Здравствуйте, {self.state.name}")
        return True

    async def make_tx(self, to_addr, amount):
        """Транзакция с немедленным сохранением в БД"""
        if self.state.balance < amount:
            print("==> Ошибка: Недостаточно средств")
            return False
        new_tx = Tx(sender=self.state.address, to=to_addr, amount=amount)
        self.state.balance -= amount
        self.state.history.append(new_tx)
        await self.save()
        print(f"[LOG] Транзакция на {amount} DOD сохранена в историю БД")
        return True