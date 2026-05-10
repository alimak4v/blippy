import os
import asyncio
import secure_codex
import logging
from models import State, Tx
from database import DBManager
from security_vault import SecurityVault

class BankNode:
    DB1 = "storage/vault_a.bin"
    DB2 = "storage/vault_b.bin"

    def __init__(self):
        self.state = None
        self.db = DBManager("storage/xbank.db")
        os.makedirs("storage", exist_ok=True)

    async def save(self):
        """Кодируем зеркала + сохраняем в SQLite + Защита Keyring"""
        data_json = self.state.model_dump_json()
        with open(self.DB1, "wb") as f:
            f.write(secure_codex.encoder1(data_json).encode('latin1'))
        with open(self.DB2, "wb") as f:
            f.write(secure_codex.encoder2(data_json).encode('latin1'))
        await self.db.save_all(self.state)
        SecurityVault.protect_balance(self.state.name, self.state.balance)
        print("==> Данные синхронизированы и защищены в Keyring")

    async def startup(self):
        """Импорт, тройная проверка и проверка Keyring"""
        await self.db.init_db()
        if not os.path.exists(self.DB1) or not os.path.exists(self.DB2):
            print("==> Файлы не найдены. Создаю новый кошелек")
            return False
        with open(self.DB1, "rb") as f:
            d1 = secure_codex.decoder1(f.read().decode('latin1'))
        with open(self.DB2, "rb") as f:
            d2 = secure_codex.decoder2(f.read().decode('latin1'))
        db_state = await self.db.load_state()
        if not SecurityVault.verify_integrity(db_state.name, db_state.balance):
            logging.error("КРИТИЧЕСКАЯ ОШИБКА: Обнаружена попытка подделки баланса в БД!")
            raise Exception("DATABASE_CORRUPTED_OR_TAMPERED")
        db_data_json = db_state.model_dump_json()
        if d1 != d2 or d1 != db_data_json:
            logging.error("КРИТИЧЕСКАЯ ОШИБКА: Расхождение данных в зеркалах или БД!")
            raise Exception("УСТАНОВЛЕНА ПОПЫТКА ИЗМЕНЕНИЯ БАЛАНСА")
        self.state = State.model_validate_json(d1)
        print(f"==> Проверка пройдена. Баланс подтвержден. Здравствуйте, {self.state.name}")
        return True

    async def make_tx(self, to_addr, amount):
        """Транзакция"""
        if self.state.balance < amount:
            print("==> Ошибка: Недостаточно средств")
            return False
        new_tx = Tx(sender=self.state.address, to=to_addr, amount=amount)
        self.state.balance -= amount
        self.state.history.append(new_tx)
        await self.save()
        print(f"[LOG] Транзакция на {amount} DOD сохранена.")
        return True

    async def receive_payment(self, tx_data):
        """ Обработка входящей транзакции """
        if not tx_data:
            print("Получены битые данные.")
            return
        sender = tx_data.get("sender", "Unknown")
        amount = tx_data.get("amount", 0)
        print(f"Пришли деньги: {amount} Ð от {sender}")
        self.state.balance += amount
        new_tx = Tx(sender=sender, to=self.state.address, amount=amount)
        self.state.history.append(new_tx)
        await self.save()
        print(f"[LOG] Баланс успешно обновлен и защищен.")