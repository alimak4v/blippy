import asyncio
from bleak import BleakScanner

NODE_PREFIX = "node-"
RSSI_REQUIREMENT = -80

async def find_nearby_users():
    """ Сканирует эфир Bluetooth и возвращает список узлов."""
    print("Сканирование... (подожди 3 сек)")
    
    devices = await BleakScanner.discover(timeout=3.0, return_adv=True)
    
    found_users = []
    
    for address, (device, adv_data) in devices.items():
        name = device.name or "Unknown"
        rssi = adv_data.rssi

        if name.startswith(NODE_PREFIX) and rssi > RSSI_REQUIREMENT:
            found_users.append({
                "address": address,
                "name": name,
                "rssi": rssi
            })
            
    return found_users
