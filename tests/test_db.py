import pytest
import pytest_asyncio
import aiosqlite
from database import DBManager
from models import Tx, State
import logging


@pytest_asyncio.fixture
async def db_manager(tmp_path):
    """Создаёт DBManager с временной БД."""
    db_path = tmp_path / "test_xbank.db"
    manager = DBManager(str(db_path))
    await manager.init_db()
    return manager


@pytest_asyncio.fixture
async def empty_db_manager(db_manager):
    """Пустая БД (только инициализирована)."""
    return db_manager


@pytest_asyncio.fixture
async def populated_db_manager(db_manager):
    """БД с тестовыми данными."""
    async with aiosqlite.connect(db_manager.db_path) as db:
        await db.execute(
            "INSERT INTO state (id, name, address, balance) VALUES (1, 'Alice', '0x123', 100.5)"
        )
        await db.execute(
            "INSERT INTO history (sender, recipient, amount) VALUES ('0x123', '0x456', 10.0)"
        )
        await db.execute(
            "INSERT INTO history (sender, recipient, amount) VALUES ('0x123', '0x789', 20.5)"
        )
        await db.commit()
    return db_manager


@pytest.mark.asyncio
async def test_init_db_creates_tables(empty_db_manager):
    """Проверяет, что init_db создаёт таблицы."""
    async with aiosqlite.connect(empty_db_manager.db_path) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='state'")
        assert await cursor.fetchone() is not None
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
        assert await cursor.fetchone() is not None


@pytest.mark.asyncio
async def test_load_state_empty_db(empty_db_manager):
    """При пустой БД load_state возвращает дефолтное состояние без истории."""
    state = await empty_db_manager.load_state()
    assert state.name == "New User"
    assert state.address == "0x0"
    assert state.balance == 0.0
    assert state.history == []


@pytest.mark.asyncio
async def test_load_state_populated_db(populated_db_manager):
    """Загружает существующие данные из БД."""
    state = await populated_db_manager.load_state()
    assert state.name == "Alice"
    assert state.address == "0x123"
    assert state.balance == 100.5
    assert len(state.history) == 2
    assert state.history[0].sender == "0x123"
    assert state.history[0].to == "0x456"
    assert state.history[0].amount == 10.0
    assert state.history[1].sender == "0x123"
    assert state.history[1].to == "0x789"
    assert state.history[1].amount == 20.5


@pytest.mark.asyncio
async def test_save_all_overwrites_state(empty_db_manager):
    """save_all перезаписывает state и историю, удаляя старые записи."""
    state1 = State(name="Bob", address="0xabc", balance=50.0, history=[])
    await empty_db_manager.save_all(state1)

    history2 = [
        Tx(sender="0xabc", to="0xdef", amount=12.0),
        Tx(sender="0xabc", to="0x111", amount=8.0)
    ]
    state2 = State(name="Charlie", address="0x222", balance=30.0, history=history2)
    await empty_db_manager.save_all(state2)
    loaded = await empty_db_manager.load_state()
    assert loaded.name == "Charlie"
    assert loaded.address == "0x222"
    assert loaded.balance == 30.0
    assert len(loaded.history) == 2
    assert loaded.history[0].sender == "0xabc"
    assert loaded.history[0].to == "0xdef"
    assert loaded.history[0].amount == 12.0


@pytest.mark.asyncio
async def test_save_all_empty_history(empty_db_manager):
    """Сохраняет состояние с пустой историей, удаляя предыдущие транзакции."""
    state_with_history = State(
        name="Dave", address="0x333", balance=100.0,
        history=[Tx(sender="0x333", to="0x444", amount=25.0)]
    )
    await empty_db_manager.save_all(state_with_history)
    state_no_history = State(name="Eve", address="0x555", balance=0.0, history=[])
    await empty_db_manager.save_all(state_no_history)
    loaded = await empty_db_manager.load_state()
    assert loaded.name == "Eve"
    assert loaded.balance == 0.0
    assert loaded.history == []
    async with aiosqlite.connect(empty_db_manager.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM history")
        count = (await cursor.fetchone())[0]
        assert count == 0

@pytest.mark.asyncio
async def test_load_state_logs_when_no_data(caplog, empty_db_manager):
    """При отсутствии данных load_state логирует сообщение."""
    caplog.set_level(logging.INFO)
    await empty_db_manager.load_state()
    assert "Данные не найдены. Возвращаем дефолтное состояние." in caplog.text


@pytest.mark.asyncio
async def test_save_all_logs_final_balance(caplog, empty_db_manager):
    """save_all логирует финальный баланс."""
    caplog.set_level(logging.INFO)
    state = State(name="Test", address="0x1", balance=123.45, history=[])
    await empty_db_manager.save_all(state)
    assert "Финальный баланс: 123.45" in caplog.text
