<div align="center">

# Blippy

### Offline P2P wallet over Bluetooth

**Blippy lets nearby devices discover each other and exchange local transactions directly over Bluetooth Low Energy — without a central server or internet connection.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C++-native%20module-00599C?logo=cplusplus&logoColor=white)](https://isocpp.org/)
[![Bluetooth LE](https://img.shields.io/badge/Bluetooth-LE-0082FC?logo=bluetooth&logoColor=white)](https://www.bluetooth.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

</div>

> [!IMPORTANT]
> Blippy is an educational prototype. It does not use a blockchain, does not provide consensus between nodes, and must not be used to store or transfer real money.

## About

Blippy explores what a fully local digital wallet could look like. Each device acts as an independent node: it advertises itself over BLE, discovers nearby users, sends and receives transactions, and stores its wallet state locally.

The project combines a desktop interface, asynchronous Python networking, a native C++ codec, SQLite persistence, and integrity checks through the operating system keyring.

## How it works

1. The user creates a wallet with a local nickname.
2. Blippy starts a Bluetooth GATT server and advertises the node.
3. The app scans for nearby wallets with the `node-` prefix.
4. The sender selects a recipient and enters an amount.
5. The transaction is serialized as JSON and sent through a BLE characteristic.
6. Both nodes update their local balance and transaction history.
7. The state is written to SQLite and two encoded mirror files, then verified against a SHA-256 fingerprint stored in the OS keyring.

## Features

- **Direct BLE transfers** — nearby devices communicate without a backend.
- **Nearby wallet discovery** — scan and filter nodes by name and signal strength.
- **Desktop GUI** — view the address, balance, nearby users, and transaction history.
- **Asynchronous core** — Bluetooth, storage, and UI events are coordinated with `asyncio`.
- **Local persistence** — wallet state and history are stored in SQLite.
- **Triple state verification** — SQLite is checked against two independently encoded mirror files.
- **OS-level integrity fingerprint** — the balance hash is stored using `keyring`.
- **Native C++ module** — mirror encoding and decoding are exposed to Python through pybind11.
- **Tests and profiling** — the project includes pytest suites and a cProfile load script.
- **Docker environment** — Linux containers can access Bluetooth, D-Bus, and the X11 GUI.

## Architecture

```text
PySimpleGUI
    │
    ▼
 BlippyApp ───────────────► BLE scanner (bleak)
    │
    ▼
 BankNode ◄─────────────── BLE GATT server (bless)
    │
    ├── SQLite database
    ├── C++ encoded mirror A
    ├── C++ encoded mirror B
    └── SHA-256 fingerprint in OS keyring
```

| Module | Responsibility |
|---|---|
| `source/main.py` | Desktop UI, application lifecycle, and async coordination |
| `source/scanner.py` | Discovery of nearby Blippy nodes |
| `source/server.py` | BLE GATT server for incoming transactions |
| `source/transfer.py` | Connection and transaction delivery to another node |
| `source/protocol.py` | JSON transaction serialization |
| `source/manager.py` | Balance, history, persistence, and integrity orchestration |
| `source/database.py` | Asynchronous SQLite storage |
| `source/secret_vault.py` | SHA-256 fingerprint storage and verification |
| `source/secure_codex.cpp` | Native encoding and decoding of state mirrors |

## Tech stack

- Python 3.11
- C++11 and pybind11
- Bluetooth Low Energy: Bleak + Bless
- GUI: PySimpleGUI
- Storage: SQLite + aiosqlite
- Validation: Pydantic
- System keyring: keyring
- Testing: pytest + pytest-asyncio
- Containers: Docker Compose

## Running with Docker

### Requirements

The provided container setup targets **Linux** and expects:

- a working Bluetooth adapter available as `/dev/hci0`;
- D-Bus available at `/var/run/dbus`;
- an X11 session for the desktop interface;
- Docker and Docker Compose.

Allow the container to connect to the local X server:

```bash
xhost +local:docker
```

Build and start Blippy:

```bash
docker compose up --build
```

Wallet data is persisted in `storage/` and `database.db`.

## Running locally

Install the system dependencies for Bluetooth, Tk, a C++ compiler, and Python development headers. Then create a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pybind11
```

Build the native codec from the repository root:

```bash
g++ -O3 -Wall -shared -std=c++11 -fPIC \
  $(python3 -m pybind11 --includes) \
  source/secure_codex.cpp \
  -o source/secure_codex$(python3-config --extension-suffix)
```

Start the application:

```bash
python3 -m source.main
```

> Bluetooth peripheral support depends on the operating system and adapter. The current setup is primarily designed for Linux.

## Tests

```bash
pytest
```

Run the profiling scenario:

```bash
python profile_script.py
```

## Current limitations

Blippy currently models transactions locally and intentionally keeps the protocol simple. In particular:

- there is no distributed ledger or global source of truth;
- transactions are not digitally signed;
- peers are not cryptographically authenticated;
- balances can diverge after interrupted or malicious transfers;
- XOR-based mirror encoding provides redundancy, not encryption;
- floating-point values are used for amounts;
- cross-platform BLE behavior may differ.

These constraints make Blippy suitable for studying P2P networking, local-first architecture, asynchronous applications, and tamper detection — but not for financial use.

## Roadmap

- [ ] Cryptographic identities and signed transactions
- [ ] Atomic acknowledgement protocol for transfers
- [ ] Replay protection and transaction IDs
- [ ] Fixed-point amount representation
- [ ] Peer authentication and encrypted payloads
- [ ] Recovery flow for corrupted local state
- [ ] Improved cross-platform Bluetooth support
- [ ] Packaging and automated releases

## Authors

Built by **Алексей**, **Борис Осин**, and **Матвей Вербицкий** as a collaborative educational project.

---

<div align="center">

**Local-first. Serverless. Nearby.**

</div>
