# netscope-py

> **RU** | [EN](#english)

---

## Русский

Тонкая Python-обертка над бинарником **netscope-scan** — форком RustScan без nmap и скриптинга. Бинарник принимает цели, сканирует порты и возвращает чистый JSON; эта библиотека превращает его в удобный Python-API с полной типизацией.

### Требования

- Python ≥ 3.12
- Бинарник `netscope-scan` в `PATH` **или** переменная окружения `NETSCOPE_BIN`

### Установка

```bash
# из исходников (editable)
uv pip install -e .

# сборка wheel
uv build
```

### Быстрый старт

```python
from netscope import scan, scan_async, ScanResult, ScanError

# --- Синхронный вызов ---
results: list[ScanResult] = scan(
    ["192.168.1.0/24", "10.0.0.1"],
    ports=[22, 80, 443],
)

for r in results:
    print(r.ip, r.ports)
# 192.168.1.5   [22, 80]
# 10.0.0.1      [22, 443]

# --- Асинхронный вызов ---
import asyncio

async def main() -> None:
    results = await scan_async(["10.0.0.0/24"], range=(1, 1000))
    for r in results:
        print(r.ip, r.ports)

asyncio.run(main())
```

### Справочник API

#### `scan(addresses, *, ...)` → `list[ScanResult]`

Синхронное сканирование. Блокирует поток до завершения бинарника.

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `addresses` | `list[str]` | — | Цели: IP, CIDR, хосты |
| `ports` | `list[int] \| None` | `None` | Конкретные порты |
| `range` | `tuple[int, int] \| None` | `None` | Диапазон портов `(start, end)` включительно |
| `top` | `bool` | `False` | Топ-1000 популярных портов |
| `batch_size` | `int` | `4500` | Одновременных сокетов |
| `timeout` | `int` | `1500` | Таймаут на порт, мс |
| `tries` | `int` | `1` | Попыток на порт |
| `ulimit` | `int \| None` | `None` | Лимит файловых дескрипторов (Unix) |
| `scan_order` | `str` | `"serial"` | `"serial"` или `"random"` |
| `exclude_ports` | `list[int] \| None` | `None` | Исключить порты |
| `exclude_addresses` | `list[str] \| None` | `None` | Исключить адреса/CIDR |
| `udp` | `bool` | `False` | UDP-режим |
| `resolver` | `str \| None` | `None` | Кастомные DNS-резолверы |

> **Приоритет выбора портов:** `ports` > `range` > `top`. Если задано несколько — используется первое ненулевое.

#### `scan_async(addresses, *, ...)` → `Awaitable[list[ScanResult]]`

Асинхронная версия. Принимает те же аргументы, что и `scan`. Использует `asyncio.create_subprocess_exec` — event loop не блокируется.

#### `ScanResult`

```python
@dataclass
class ScanResult:
    ip: str        # IP-адрес хоста
    ports: list[int]  # Открытые порты
```

#### `ScanError`

Наследует `RuntimeError`. Выбрасывается, если `netscope-scan` завершился с ненулевым кодом. Сообщение содержит вывод stderr.

```python
try:
    results = scan(["10.0.0.1"], ports=[80])
except ScanError as e:
    print(e)  # netscope-scan error output
```

### Расположение бинарника

Порядок поиска:

1. Переменная окружения `NETSCOPE_BIN`
2. Файл `bin/netscope-scan` внутри установленного пакета
3. `netscope-scan` в `PATH`

```bash
# Явно указать путь
NETSCOPE_BIN=/opt/tools/netscope-scan python my_script.py
```

### Примеры

```python
# Сканирование подсети, случайный порядок
results = scan(
    ["10.10.0.0/16"],
    range=(1, 65535),
    batch_size=8000,
    timeout=800,
    scan_order="random",
    ulimit=65536,
)

# Исключить служебные адреса
results = scan(
    ["192.168.0.0/24"],
    top=True,
    exclude_addresses=["192.168.0.1", "192.168.0.254"],
    exclude_ports=[135, 139, 445],
)

# UDP
results = scan(["10.0.0.1"], ports=[53, 161, 500], udp=True)

# Несколько целей параллельно (asyncio)
import asyncio

async def multi_scan() -> None:
    tasks = [
        scan_async(["10.0.0.0/24"], ports=[22]),
        scan_async(["172.16.0.0/24"], ports=[80, 443]),
    ]
    all_results = await asyncio.gather(*tasks)
    for batch in all_results:
        for r in batch:
            print(r.ip, r.ports)

asyncio.run(multi_scan())
```

---

## English

<a name="english"></a>

A thin Python wrapper around **netscope-scan** — a RustScan fork with nmap and scripting removed. The binary accepts targets, scans ports, and emits clean JSON; this library turns it into a typed Python API.

### Requirements

- Python ≥ 3.12
- `netscope-scan` binary on `PATH` **or** `NETSCOPE_BIN` environment variable

### Installation

```bash
# editable install from source
uv pip install -e .

# build a wheel
uv build
```

### Quick start

```python
from netscope import scan, scan_async, ScanResult, ScanError

# --- Synchronous ---
results: list[ScanResult] = scan(
    ["192.168.1.0/24", "10.0.0.1"],
    ports=[22, 80, 443],
)

for r in results:
    print(r.ip, r.ports)
# 192.168.1.5   [22, 80]
# 10.0.0.1      [22, 443]

# --- Asynchronous ---
import asyncio

async def main() -> None:
    results = await scan_async(["10.0.0.0/24"], range=(1, 1000))
    for r in results:
        print(r.ip, r.ports)

asyncio.run(main())
```

### API reference

#### `scan(addresses, *, ...)` → `list[ScanResult]`

Synchronous port scan. Blocks the calling thread until the binary exits.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `addresses` | `list[str]` | — | Targets: IPs, CIDRs, hostnames |
| `ports` | `list[int] \| None` | `None` | Explicit port list |
| `range` | `tuple[int, int] \| None` | `None` | Port range `(start, end)` inclusive |
| `top` | `bool` | `False` | Scan top-1000 common ports |
| `batch_size` | `int` | `4500` | Concurrent socket count |
| `timeout` | `int` | `1500` | Per-port timeout in ms |
| `tries` | `int` | `1` | Probe attempts per port |
| `ulimit` | `int \| None` | `None` | File-descriptor limit (Unix) |
| `scan_order` | `str` | `"serial"` | `"serial"` or `"random"` |
| `exclude_ports` | `list[int] \| None` | `None` | Ports to skip |
| `exclude_addresses` | `list[str] \| None` | `None` | Addresses/CIDRs to skip |
| `udp` | `bool` | `False` | UDP mode |
| `resolver` | `str \| None` | `None` | Custom DNS resolvers |

> **Port selection priority:** `ports` > `range` > `top`. The first non-`None` / truthy value wins.

#### `scan_async(addresses, *, ...)` → `Awaitable[list[ScanResult]]`

Async variant with identical parameters. Uses `asyncio.create_subprocess_exec` — the event loop is never blocked.

#### `ScanResult`

```python
@dataclass
class ScanResult:
    ip: str           # Host IP address
    ports: list[int]  # Open port numbers
```

#### `ScanError`

Subclass of `RuntimeError`. Raised when `netscope-scan` exits with a non-zero code. The error message includes the binary's stderr output.

```python
try:
    results = scan(["10.0.0.1"], ports=[80])
except ScanError as e:
    print(e)  # netscope-scan error output
```

### Binary resolution

The binary is located in this order:

1. `NETSCOPE_BIN` environment variable
2. `bin/netscope-scan` bundled inside the installed package
3. `netscope-scan` anywhere on `PATH`

```bash
# Point to a custom binary
NETSCOPE_BIN=/opt/tools/netscope-scan python my_script.py
```

### Examples

```python
# Large subnet, random order, raised ulimit
results = scan(
    ["10.10.0.0/16"],
    range=(1, 65535),
    batch_size=8000,
    timeout=800,
    scan_order="random",
    ulimit=65536,
)

# Exclude gateway and broadcast, skip Windows noise ports
results = scan(
    ["192.168.0.0/24"],
    top=True,
    exclude_addresses=["192.168.0.1", "192.168.0.254"],
    exclude_ports=[135, 139, 445],
)

# UDP scan
results = scan(["10.0.0.1"], ports=[53, 161, 500], udp=True)

# Run multiple subnets in parallel with asyncio
import asyncio

async def multi_scan() -> None:
    tasks = [
        scan_async(["10.0.0.0/24"], ports=[22]),
        scan_async(["172.16.0.0/24"], ports=[80, 443]),
    ]
    all_results = await asyncio.gather(*tasks)
    for batch in all_results:
        for r in batch:
            print(r.ip, r.ports)

asyncio.run(multi_scan())
```

### Project structure

```
netscope-py/
├── pyproject.toml
└── src/
    └── netscope/
        ├── __init__.py   # Public re-exports: scan, scan_async, ScanResult, ScanError
        ├── _models.py    # ScanResult dataclass, ScanError exception
        ├── _runner.py    # subprocess / asyncio implementation
        └── py.typed      # PEP 561 marker — full type information shipped
```
