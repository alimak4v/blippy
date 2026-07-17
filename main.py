import sys
import asyncio
from manager import BankNode
from models import State
from scanner import find_nearby_users
from transfer import send_transaction
from server import WalletNode

async def main():
    node = BankNode()

    try:
        if not await node.startup():
            name = input("Введите ник: ")
            for s in name:
                if (s < 'a' or s > 'z') and (s < "A" or s > "Z"):
                    raise Exception("В нике могут быть только строчнве и заглавные буквы")
            node.state = State(name=name, address="node-"+name, balance=100.0)
            await node.save()
    except Exception as e:
        print(e)
        sys.exit()

    print("Запуск Bluetooth-сервера")
    server = WalletNode(node.receive_payment)
    await server.start(node.state.address)

    while True:
        print(f"\nКошелек: {node.state.address}\nБаланс: {node.state.balance} Ð")
        print("1 - Отправить Ð\n2 - История\n3 - Выход\n4 - Поиск ближайших пользователей")
        choice = input(">> ")

        if choice == "1":
            print("Поиск получателей рядом...")
            users = await find_nearby_users()
            
            if not users:
                print("Никого не найдено.")
                continue
            
            print("\nВыберите получателя:")
            for i, user in enumerate(users, 1):
                print(f"  {i}. {user['name']} (сигнал: {user['rssi']})")
            
            try:
                idx = int(input("Номер: ")) - 1
                if idx < 0 or idx >= len(users):
                    print("Неверный номер")
                    continue
                
                target = users[idx]
                amount = float(input("Сумма: "))
                
                print(f"Отправка {amount} Ð на {target['name']}...")
                
                success = await send_transaction(
                    target['address'],
                    node.state.address,
                    target['name'],
                    amount
                )
                
                if success:
                    await node.make_tx(target['address'], amount)
                    print("Транзакция завершена!")
                else:
                    print("Ошибка отправки.")
                    
            except ValueError:
                print("Ошибка ввода.")
            except Exception as e:
                print(f"Ошибка: {e}")

        elif choice == "2":
            if not node.state.history:
                print("История пуста.")
            for t in node.state.history:
                print(f"Перевод: {t.amount} -> {t.to}")

        elif choice == "3":
            await node.save()
            await server.stop()
            print("Данные сохранены. До свидания!")
            break
        
        elif choice == "4":
            users = await find_nearby_users()
            
            if not users:
                print("По близости нет ни одного пользователя.")
            else:
                print(f"Найдено пользователей: {len(users)}")
                for user in users:
                    print(f"{user['name']} (Сигнал: {user['rssi']})")



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass