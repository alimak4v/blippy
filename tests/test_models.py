import pytest
import json

from source.models import State, Tx

def test_valid_creation():
    '''Проверка корректного создания транзакции'''
    tx = Tx(sender="node-Alex", to="node-Boris", amount=50.0)

    assert tx.sender == "node-Alex"
    assert tx.to == "node-Boris"
    assert tx.amount == 50.0


def test_state_creation_and_defaults():
    '''Создание состояния и проверка дефолтов'''
    state = State(name="Alex", address="node-Alex", balance=100.0)

    assert state.balance == 100.0
    assert state.name == "Alex"
    assert isinstance(state.history, list)
    assert len(state.history) == 0


def test_state_history_append():
    '''Добавление транзакций в историю'''
    state = State(name="Boris", address="node-Boris", balance=0.0)

    tx1 = Tx(sender="node-Alex", to="node-Boris", amount=10.0)
    tx2 = Tx(sender="node-Matvey", to="node-Boris", amount=20.0)
    
    state.history.append(tx1)
    state.history.append(tx2)
    
    assert len(state.history) == 2
    assert state.history[0].sender == "node-Alex"
    assert state.history[0].amount == 10.0
    assert state.history[1].sender == "node-Matvey"
    assert state.history[1].amount == 20.0


def test_state_serialization_json():
    '''Проверка сериализации для БД и SecretVault'''
    state = State(
        name="Matvey",
        address="node-Matvey",
        balance=99.9,
        history=[Tx(sender="node-Alex", to="node-Matvey", amount=5.0)]
    )
    
    json_str = state.model_dump_json()
    data = json.loads(json_str)
    
    assert data["balance"] == 99.9
    assert data["name"] == "Matvey"
    assert len(data["history"]) == 1
    assert data["history"][0]["amount"] == 5.0


def test_state_deserialization_from_dict():
    '''Обратная проверка: загрузка из словаря'''
    raw_data = {
        "name": "Boris",
        "address": "node-Boris",
        "balance": 200.0,
        "history": [{"sender": "node-Matvey", "to": "node-Boris", "amount": 25.0}]
    }
    
    state = State(**raw_data)

    assert state.balance == 200.0
    assert state.name == "Boris"
    assert state.history[0].sender == "node-Matvey"
    assert state.history[0].amount == 25.0