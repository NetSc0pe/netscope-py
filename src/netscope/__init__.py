"""netscope — Python wrapper for the netscope-scan port scanner.

Public API
----------
:func:`scan`
    Synchronous port scan. Blocks until the binary exits.

:func:`scan_async`
    Asynchronous port scan. Awaitable; does not block the event loop.

:class:`~netscope.models.ScanResult`
    Dataclass holding the IP and list of open ports for a single host.

:exc:`~netscope.models.ScanError`
    Raised when netscope-scan exits with a non-zero return code.

Quick start::

    from netscope import scan, scan_async, ScanResult, ScanError

    # Synchronous
    results: list[ScanResult] = scan(
        ["192.168.1.0/24"],
        ports=[22, 80, 443],
    )

    # Asynchronous
    import asyncio
    results = asyncio.run(scan_async(["10.0.0.1"], range=(1, 1000)))

Binary location
---------------
The binary is resolved in this order:

1. ``NETSCOPE_BIN`` environment variable.
2. ``bin/netscope-scan`` bundled inside the installed package.
3. ``netscope-scan`` found anywhere on ``PATH``.
"""

from netscope._models import ScanError, ScanResult
from netscope._runner import scan, scan_async

__all__ = ["scan", "scan_async", "ScanResult", "ScanError"]
