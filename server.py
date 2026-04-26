import asyncio
from uuid import UUID
from bleak import BleakServer
from protocol import unpack_transaction
from bleak.backends.service import BleakGATTServiceCollection
from bleak.backends.characteristic import BleakGATTCharacteristic

SERVICE_UUID = UUID("A0B1C2D3-E4F5-46A7-B8C9-D0E1F2A3B4C5")
CHAR_UUID = UUID("1A2B3C4D-5E6F-47A8-B9C0-D1E2F3A4B5C6")

class WalletNode:
    def __init__(self, transaction_callback):
        self.callback = transaction_callback
        self.server = None

    async def start(self, name):
        services = BleakGATTServiceCollection()
        service = BleakGATTService(SERVICE_UUID)
        
        char = BleakGATTCharacteristic(
            CHAR_UUID,
            ["write"],
            service_uuid=SERVICE_UUID
        )
        
        char._write_gatt = self.on_write
        
        service.add_characteristic(char)
        services.add_service(service)
        
        self.server = BleakServer(name, services)
        await self.server.start()

    async def on_write(self, client, data):
        print(f"Получены данные от {client.address}")

        parsed_data = unpack_transaction(data)
        
        if self.callback:
            await self.callback(parsed_data)

    async def stop(self):
        if self.server:
            await self.server.stop()
