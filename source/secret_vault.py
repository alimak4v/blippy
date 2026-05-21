import keyring
import hashlib


class SecurityVault:
    SERVICE_NAME = "XBank_System"

    @staticmethod
    def protect_balance(username: str, balance: float):
        """Создает хеш-отпечаток баланса и прячет его в системное хранилище ОС"""
        balance_data = f"{username}:{balance}"
        balance_hash = hashlib.sha256(balance_data.encode()).hexdigest()
        keyring.set_password(SecurityVault.SERVICE_NAME, f"{username}_v2_hash", balance_hash)

    @staticmethod
    def verify_integrity(username: str, current_balance: float) -> bool:
        """Сверяет баланс из БД с отпечатком в системном сейфе"""
        stored_hash = keyring.get_password(SecurityVault.SERVICE_NAME, f"{username}_v2_hash")
        if not stored_hash:
            return True
        current_hash = hashlib.sha256(f"{username}:{current_balance}".encode()).hexdigest()
        return stored_hash == current_hash
