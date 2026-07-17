import asyncio
from bleak import BleakClient

from source.protocol import pack_transaction

CHAR_UUID = "1A2B3C4D-5E6F-47A8-B9C0-D1E2F3A4B5C6"

async def send_transaction(target_address, sender, reciever, amount):
    print("Попытка подключения")
    client = BleakClient(target_address)
    
    try:
        await client.connect(timeout=10.0)
        print("Подключено!")
        data = pack_transaction(sender, reciever, amount)
        await client.write_gatt_char(CHAR_UUID, data, response=True)
        print("Данные отправлены!")
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    finally:
        print("Отключение")
        await client.disconnect()
