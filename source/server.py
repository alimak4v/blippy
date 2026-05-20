import asyncio
from bless import BlessServer, GATTCharacteristicProperties, GATTAttributePermissions

SERVICE_UUID = "A0B1C2D3-E4F5-46A7-B8C9-D0E1F2A3B4C5"
CHAR_UUID = "1A2B3C4D-5E6F-47A8-B9C0-D1E2F3A4B5C6"

class WalletNode:
    def __init__(self, transaction_callback):
        self.callback = transaction_callback
        self.server = None

    async def start(self, name):
        loop = asyncio.get_running_loop()
        # тут была бага с тем, что окно якобы зависало с "инициализация..."
        try:
            self.server = await asyncio.wait_for(
                asyncio.to_thread(BlessServer, name, loop),
                timeout=45.0,
            )
        except asyncio.TimeoutError:
            raise RuntimeError("Bluetooth не отвечает.")

        await self.server.add_new_service(SERVICE_UUID)
        
        properties = (
            GATTCharacteristicProperties.read |
            GATTCharacteristicProperties.write |
            GATTCharacteristicProperties.write_without_response
        )
        
        permissions = [
            GATTAttributePermissions.readable,
            GATTAttributePermissions.writeable
        ]
        
        await self.server.add_new_characteristic(
            SERVICE_UUID,
            CHAR_UUID,
            properties,
            None,
            permissions
        )
        
        self.server.write_request_func = self.on_write
        
        await self.server.start()

    def on_write(self, characteristic, value):
        """Вызывается при получении байтов по Bluetooth"""
        print(f"Получены данные транзакции...")
        if self.callback:
            from protocol import unpack_transaction
            try:
                parsed_data = unpack_transaction(value)
                srv_loop = getattr(self.server, "loop", None) if self.server else None
                if srv_loop is not None:
                    asyncio.run_coroutine_threadsafe(self.callback(parsed_data), srv_loop)
                else:
                    asyncio.create_task(self.callback(parsed_data))
            except Exception as e:
                print(f"Ошибка обработки данных: {e}")

    async def stop(self):
        """Остановка сервера"""
        if self.server:
            await self.server.stop()
