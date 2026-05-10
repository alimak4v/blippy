import asyncio
import threading
from typing import Any

import PySimpleGUI as sg

from manager import BankNode
from models import State
from scanner import find_nearby_users
from server import WalletNode
from transfer import send_transaction


def _valid_nickname(name: str) -> bool:
    if not name:
        return False
    for ch in name:
        if (ch < "a" or ch > "z") and (ch < "A" or ch > "Z"):
            return False
    return True


def _make_payment_callback(window: sg.Window, node: BankNode):
    async def on_payment(tx_data: dict[str, Any] | None):
        await node.receive_payment(tx_data)
        window.write_event_value("-BALANCE_CHANGED-", "")

    return on_payment


class BlippyApp:
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self.node: BankNode | None = None
        self.server: WalletNode | None = None
        self.name_future: asyncio.Future | None = None
        self.nearby_users: list[dict[str, Any]] = []
        self.shutdown = asyncio.Event()
        self.window: sg.Window | None = None

    def run(self) -> None:
        sg.theme("DarkGrey5")
        self.window = sg.Window(
            "Blippy — кошелёк",
            self._layout(),
            finalize=True,
            resizable=True,
        )
        # ошибка с disabled/enabled кнопками
        self._set_ble_actions_enabled(False)
        self.window["-HIST-"].update(disabled=True)
        self._set_status("Инициализация…")
        threading.Thread(target=self._async_thread_main, daemon=True).start()
        self._gui_loop()
        if self.window:
            self.window.close()

    def _layout(self) -> list[list[sg.Element]]:
        return [
            [sg.Text("", key="-STATUS-", size=(55, 1))],
            [
                sg.Text("Адрес:", size=(8, 1)),
                sg.Text("", key="-ADDR-", size=(45, 1)),
            ],
            [
                sg.Text("Баланс:", size=(8, 1)),
                sg.Text("", key="-BAL-", size=(45, 1)),
            ],
            [sg.HorizontalSeparator()],
            [
                sg.Text("Рядом:"),
                sg.Button("Найти получателей", key="-SCAN-"),
            ],
            [
                sg.Listbox(
                    values=[],
                    key="-USERS-",
                    size=(60, 8),
                    enable_events=True,
                )
            ],
            [
                sg.Text("Ð:"),
                sg.Input(key="-AMOUNT-", size=(12, 1)),
                sg.Button("Перевести", key="-SEND-"),
            ],
            [sg.HorizontalSeparator()],
            [
                sg.Button("История", key="-HIST-"),
                sg.Push(),
                sg.Button("Выход", key="-EXIT-"),
            ],
        ]

    def _set_status(self, text: str) -> None:
        if self.window:
            self.window["-STATUS-"].update(text)

    def _set_ble_actions_enabled(self, enabled: bool) -> None:
        if not self.window:
            return
        for key in ("-SCAN-", "-SEND-", "-USERS-", "-AMOUNT-"):
            self.window[key].update(disabled=not enabled)

    def _refresh_wallet_ui(self) -> None:
        if not self.window or not self.node or not self.node.state:
            return
        st = self.node.state
        self.window["-ADDR-"].update(st.address)
        self.window["-BAL-"].update(f"{st.balance} Ð")

    def _gui_loop(self) -> None:
        assert self.window is not None
        while True:
            # зависало на инициализации в том числе здесь
            event, values = self.window.read(timeout=100)
            if event in (sg.TIMEOUT_KEY, sg.WIN_CLOSED, None):
                if event in (sg.WIN_CLOSED, None):
                    self._request_shutdown_and_wait()
                    break
                continue
            if event == "-ASK_NAME-":
                self._on_ask_name()
                continue
            if event == "-WALLET_LOADED-":
                self._set_status("Запуск Bluetooth-сервера…")
                self._refresh_wallet_ui()
                self.window["-HIST-"].update(disabled=False)
                continue
            if event == "-READY-":
                self._set_status("Готово. Bluetooth-сервер запущен.")
                self._set_ble_actions_enabled(True)
                self._refresh_wallet_ui()
                continue
            if event == "-FATAL-":
                sg.popup_error(values.get("-FATAL-", "Неизвестная ошибка"))
                self._request_shutdown_and_wait()
                break
            if event == "-BALANCE_CHANGED-":
                self._refresh_wallet_ui()
                continue
            if event == "-SCAN_DONE-":
                self._set_status("Сканирование завершено.")
                users = self.nearby_users
                if not users:
                    self.window["-USERS-"].update(values=[])
                    sg.popup_ok("Никого не найдено.", title="Поиск")
                else:
                    lines = [f"{u['name']}  (сигнал: {u['rssi']})" for u in users]
                    self.window["-USERS-"].update(values=lines)
                continue
            if event == "-SCAN_ERR-":
                self._set_status("Ошибка сканирования.")
                sg.popup_error(values.get("-SCAN_ERR-", "Ошибка"))
                continue
            if event == "-SEND_DONE-":
                ok = values.get("-SEND_DONE-")
                if ok:
                    sg.popup_ok("Транзакция завершена.", title="Перевод")
                else:
                    sg.popup_error("Не удалось отправить перевод.", title="Перевод")
                self._refresh_wallet_ui()
                continue
            if event == "-SEND_ERR-":
                sg.popup_error(values.get("-SEND_ERR-", "Ошибка"), title="Перевод")
                continue
            if event == "-SCAN-":
                self._run_scan()
            elif event == "-SEND-":
                self._run_send(values)
            elif event == "-HIST-":
                self._show_history()
            elif event == "-EXIT-":
                self._request_shutdown_and_wait()
                break

    def _on_ask_name(self) -> None:
        assert self.window is not None
        fut = self.name_future
        loop = self.loop
        if fut is None or loop is None:
            return
        while True:
            name = sg.popup_get_text(
                "Новый кошелёк",
                "Введите ник (только латинские буквы a–z, A–Z):",
            )
            if name is None:
                loop.call_soon_threadsafe(fut.set_exception, SystemExit(0))
                loop.call_soon_threadsafe(loop.stop)
                return
            name = name.strip()
            if _valid_nickname(name):
                loop.call_soon_threadsafe(fut.set_result, name)
                return
            sg.popup_error("В нике могут быть только строчные и заглавные буквы.")

    def _run_scan(self) -> None:
        assert self.window is not None
        loop = self.loop
        if loop is None:
            return
        self._set_status("Сканирование… подождите около 3 с.")

        def worker() -> None:
            try:
                users = asyncio.run_coroutine_threadsafe(
                    find_nearby_users(), loop
                ).result(timeout=60)
                self.nearby_users = users
                self.window.write_event_value("-SCAN_DONE-", "")
            except Exception as e:
                self.window.write_event_value("-SCAN_ERR-", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _run_send(self, values: dict) -> None:
        assert self.window is not None
        loop = self.loop
        node = self.node
        if loop is None or node is None or not node.state:
            return
        sel = values.get("-USERS-")
        if not sel:
            sg.popup_error("Выберите получателя в списке.")
            return
        line = sel[0]
        lines = [f"{u['name']}  (сигнал: {u['rssi']})" for u in self.nearby_users]
        try:
            idx = lines.index(line)
        except ValueError:
            sg.popup_error("Выберите получателя в списке.")
            return
        raw = (values.get("-AMOUNT-") or "").strip().replace(",", ".")
        try:
            amount = float(raw)
        except ValueError:
            sg.popup_error("Введите сумму числом.")
            return
        if amount <= 0:
            sg.popup_error("Сумма должна быть больше нуля.")
            return
        target = self.nearby_users[idx]
        self._set_status(f"{amount} Ð TO {target['name']}")
        async def transfer() -> bool:
            ok = await send_transaction(
                target["address"],
                node.state.address,
                target["name"],
                amount,
            )
            if ok:
                await node.make_tx(target["address"], amount)
            return ok

        def worker() -> None:
            try:
                ok = asyncio.run_coroutine_threadsafe(transfer(), loop).result(
                    timeout=120
                )
                self.window.write_event_value("-SEND_DONE-", ok)
            except Exception as e:
                self.window.write_event_value("-SEND_ERR-", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _show_history(self) -> None:
        node = self.node
        if not node or not node.state:
            return
        hist = node.state.history
        if not hist:
            sg.popup_ok("История пуста.", title="История")
            return
        lines = [f"{t.amount} Ð  FROM {t.sender} TO  {t.to}" for t in hist]
        sg.popup_scrolled(
            "\n".join(lines),
            title="История операций",
            size=(80, 30),
        )

    def _request_shutdown_and_wait(self) -> None:
        loop = self.loop
        if loop is None or loop.is_closed():
            return
        async def signal() -> None:
            self.shutdown.set()
        try:
            asyncio.run_coroutine_threadsafe(signal(), loop).result(timeout=15)
        except Exception:
            loop.call_soon_threadsafe(loop.stop)

    def _async_thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        loop.create_task(self._async_main())
        loop.run_forever()

    async def _async_main(self) -> None:
        assert self.window is not None
        loop = asyncio.get_running_loop()
        node = BankNode()
        self.node = node
        server: WalletNode | None = None
        try:
            try:
                exists = await node.startup()
            except Exception as e:
                self.window.write_event_value("-FATAL-", str(e))
                return
            if not exists:
                fut: asyncio.Future = loop.create_future()
                self.name_future = fut
                self.window.write_event_value("-ASK_NAME-", "")
                try:
                    name = await fut
                except SystemExit:
                    return
                except BaseException as e:
                    self.window.write_event_value("-FATAL-", str(e))
                    return
                node.state = State(name=name, address="node-" + name, balance=100.0)
                await node.save()
            self.window.write_event_value("-WALLET_LOADED-", "")
            server = WalletNode(_make_payment_callback(self.window, node))
            self.server = server
            try:
                await server.start(node.state.address)
            except Exception as e:
                self.window.write_event_value("-FATAL-", str(e))
                return
            self.window.write_event_value("-READY-", "")
            await self.shutdown.wait()
        finally:
            if server is not None:
                try:
                    await server.stop()
                except Exception:
                    pass
            if node.state is not None:
                try:
                    await node.save()
                except Exception:
                    pass
            loop.call_soon_threadsafe(loop.stop)


def main() -> None:
    try:
        BlippyApp().run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
