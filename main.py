import sys
import asyncio
from manager import BankNode
from models import State

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

    while True:
        print(f"\nКошелек: {node.state.address}\nБаланс: {node.state.balance} Ð")
        print("1 - Отправить Ð\n2 - История\n3 - Выход")
        choice = input(">> ")

        if choice == "1":
            target = input("Адрес получателя: ")
            try:
                amt = float(input("Сумма: "))
                if await node.make_tx(target, amt):
                    print("Транзакций осуществлена (Борис, реализуйте это)")
                else:
                    print("Ошибка: недостаточно средств.")
            except:
                print("Ошибка ввода.")

        elif choice == "2":
            if not node.state.history:
                print("История пуста.")
            for t in node.state.history:
                print(f"Перевод: {t.amount} -> {t.to}")

        elif choice == "3":
            await node.save()
            print("Данные сохранены. До свидания!")
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass