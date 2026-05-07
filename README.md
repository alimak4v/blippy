
# Что было сделано за первую итерацию.

## Алексей
**Коммит:** `Aleksei's iter 1: cpp-lib for encoding/decoding base-mirrors`

### Добавленные файлы:
*   `secure_codex.cpp` / `secure_codex.so`
*   `main.py`, `manager.py`, `models.py`
*   `.gitignore`

### Что реализовано:
*   **C++ библиотека** Я реализовал модуль `secure_codex.cpp` с логикой кодирования и декодирования (base-mirrors), скомпилировал его в `.so` для интеграции с Python.
*   **Архитектура проекта:** Ввёл модель состояния `State` в `models.py` и основной класс `BankNode` в `manager.py`.
*   **Точка входа:** Создал `main.py` для инициализации, запуска через `startup()` и базовой обработки ошибок.

---

## Борис Осин
**Коммит:** `Iter 1: Boris's part - modified`

### Добавленные файлы:
*   `manager.py`, `protocol.py`, `scanner.py`, `server.py`, `transfer.py`

### Что реализовано:
*   **Логика транзакций (`manager.py`):**
    *   Обновление баланса пользователя: `self.state.balance += amount`
    *   Создание транзакции: `new_tx = Tx(sender=sender, to=self.state.address, amount=amount)`
    *   Хранение истории: `self.state.history.append(new_tx)`
*   **Сетевой слой:**
    *   `server.py`: обработка входящих запросов.
    *   `protocol.py`: правила взаимодействия между узлами.
    *   `scanner.py`: поиск и обход сети.
*   **Переводы:** Логика отправки средств в `transfer.py`.

---

## Матвей Вербицкий
**Коммит:** `Add files via upload — async database, modified main.py (async) and manager.py`

### Изменённые файлы:
*   `main.py`, `manager.py` + БД.

### Что реализовано:
*   **Асинхронность:** Полный переход на `async/await`, асинхронные методы для нормальной работы.
*   ** База данных:** Добавлен слой асинхронного хранения данных, состояния и транзакций.
*   ** Интеграция:** Адаптация логики под async-стек, связка сети, транзакций и хранилища.

---
