import sys
from manager import BankNode
from models import State

def main():
    node = BankNode()

    try:
        if not node.startup():
            name = input("Введите ник: ")
            for s in name:
                if (s < 'a' or s > 'z') and (s < "A" or s > "Z"):
                    raise Exception("В нике могут быть только строчнве и заглавные буквы")
            node.state = State(name=name, address="node-"+name, balance=100.0)
            node.save()
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
                if node.make_tx(target, amt):
                    print("Транзакций осуществлена (Борис, реализуйте это)")
                else:
                    print("Ошибка: недостаточно средств.")
            except:
                print("Ошибка ввода.")
        elif choice == "2":
            for t in node.state.history:
                print(f"Перевод: {t.amount} -> {t.to}")
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
