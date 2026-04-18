import os
import secure_codex

from models import State, Tx


class BankNode:
    # здесь еще все нужно будет продублировать в норм БДшку
    DB1 = "storage/vault_a.bin"
    DB2 = "storage/vault_b.bin"

    def __init__(self):
        self.state = None

    def save(self):
        """Кодируем данные двумя разными ключами"""
        data_json = self.state.model_dump_json()
        with open(self.DB1, "wb") as f:
            f.write(secure_codex.encoder1(data_json).encode('latin1'))
        with open(self.DB2, "wb") as f:
            f.write(secure_codex.encoder2(data_json).encode('latin1'))
        print("==> Данные синхронизированы в зеркала")

    def startup(self):
        """Импорт + проверка зеркал"""
        if not os.path.exists(self.DB1) or not os.path.exists(self.DB2):
            print("==> Создаю новый кошелек")
            return False

        with open(self.DB1, "rb") as f:
            d1 = secure_codex.decoder1(f.read().decode('latin1'))
        with open(self.DB2, "rb") as f:
            d2 = secure_codex.decoder2(f.read().decode('latin1'))

        if d1 != d2:  # здесь главное!!! добавить проверку с базой sqlite
            raise Exception("УСТАНОВЛЕНА ПОПЫТКА ИЗМЕНЕНИЯ БАЛАНСА")

        self.state = State.model_validate_json(d1)
        print(f"==> Проверка пройдена. Здравствуйте, {self.state.name}")
        return True

    def make_tx(self, to_addr, amount):
        """Метод-заглушка для осуществления транзакции"""
        if self.state.balance < amount:
            return False

        new_tx = Tx(sender=self.state.address, to=to_addr, amount=amount)
        self.state.balance -= amount
        self.state.history.append(new_tx)

        self.save()
        return True
