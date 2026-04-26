import json

def pack_transaction(sender, to, amount):
    """Упаковывает данные в байты для отправки"""
    
    data = {
        "sender": sender,
        "receiver": to,
        "amount": amount
    }
    
    json_str = json.dumps(data)
    return json_str.encode('utf-8')


def unpack_transaction(data_bytes):
    """Распаковывает байты в словарь"""
    try:
        json_str = data_bytes.decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        print(f"Ошибка распаковки: {e}")
        return None