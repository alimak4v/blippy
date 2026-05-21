import pytest

from source.models import State, Tx
from source.manager import BankNode
from source.transfer import send_transaction

@pytest.mark.asyncio
async def test_initialization(tmp_path, monkeypatch) -> None:
    '''Тестируем инициализацию базы'''
    monkeypatch.chdir(tmp_path)

    node = BankNode()
    result = await node.startup()

    assert node.state is None


@pytest.mark.asyncio
async def test_outgoing_transaction(tmp_path, monkeypatch) -> None:
    '''Тестируем списание средств (исходящий перевод)'''
    monkeypatch.chdir(tmp_path)
    
    alex = BankNode()
    await alex.startup()
    alex.state = State(name="Alex", address="node-Alex", balance=100.0)
    
    await alex.make_tx("node-Boris", 50.0)
    
    assert alex.state.balance == 50.0
    assert len(alex.state.history) == 1
    assert alex.state.history[0].sender == "node-Alex"
    assert alex.state.history[0].to == "node-Boris"
    assert alex.state.history[0].amount == 50.0


@pytest.mark.asyncio
async def test_incoming_transaction(tmp_path, monkeypatch) -> None:
    '''Тестируем зачисление средств (входящий перевод)'''
    monkeypatch.chdir(tmp_path)
    
    boris = BankNode()
    await boris.startup()
    boris.state = State(name="Boris", address="node-Boris", balance=100.0)
    
    tx_data = {
        "sender": "node-Alex",
        "to": "node-Boris",
        "amount": 50.0
    }
    await boris.receive_payment(tx_data)
    
    assert boris.state.balance == 150.0
    assert len(boris.state.history) == 1
    assert boris.state.history[0].sender == "node-Alex"
    assert boris.state.history[0].to == "node-Boris"
    assert boris.state.history[0].amount == 50.0


@pytest.mark.asyncio
async def test_incorrect_amount(tmp_path, monkeypatch):
    '''Тестируем превышение лимита средств на счете'''
    monkeypatch.chdir(tmp_path)

    alex = BankNode()
    await alex.startup()
    alex.state = State(name="Alex", address="node-Alex", balance=100.0)

    result = await alex.make_tx("node-Boris", 150.0)

    assert result is False
    assert alex.state.balance == 100.0
    assert len(alex.state.history) == 0


@pytest.mark.asyncio
async def test_zero_balance(tmp_path, monkeypatch):
    '''Граничный случай: списание ровно под ноль'''
    monkeypatch.chdir(tmp_path)

    alex = BankNode()
    await alex.startup()
    alex.state = State(name="Alex", address="node-Alex", balance=100.0)

    result = await alex.make_tx("node-Boris", 100.0)

    assert result is True
    assert alex.state.balance == 0.0
    assert len(alex.state.history) == 1


@pytest.mark.asyncio
async def test_save_and_load(tmp_path, monkeypatch):
    '''Сохранение и восстановление состояния'''
    monkeypatch.chdir(tmp_path)

    first = BankNode()
    await first.startup()
    first.state = State(name="TestUser", address="node-Test", balance=75.5, history=[])
    first.state.history.append(Tx(sender="NodeA", to="node-Test", amount=25.0))
    await first.save()

    second = BankNode()
    await second.startup()

    assert second.state is not None
    assert second.state.balance == 75.5
    assert second.state.name == "TestUser"
    assert len(second.state.history) == 1
    assert second.state.history[0].amount == 25.0
