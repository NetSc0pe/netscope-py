"""Low-level subprocess runners that invoke the netscope-scan binary.

This module is private. Consume :func:`netscope.scan` and
:func:`netscope.scan_async` from the public API instead.

Binary resolution order:

1. ``NETSCOPE_BIN`` environment variable — used as-is when set.
2. ``src/netscope/bin/netscope-scan`` — bundled binary shipped with the wheel.
3. ``shutil.which("netscope-scan")`` — searches ``PATH``.
"""

import asyncio
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from netscope._models import ScanError, ScanResult


def _binary() -> str:
    """Locate the netscope-scan executable.

    Tries, in order:

    1. The ``NETSCOPE_BIN`` environment variable.
    2. A binary bundled inside the installed package at ``bin/netscope-scan``.
       If found, the executable bit is set automatically.
    3. ``shutil.which("netscope-scan")`` (searches ``PATH``).

    Returns:
        Absolute path (or bare name, for PATH-found binaries) of the
        netscope-scan executable.

    Raises:
        RuntimeError: If the binary cannot be found by any of the three methods.
    """
    if env := os.environ.get("NETSCOPE_BIN"):
        return env

    bundled = Path(__file__).parent / "bin" / "netscope-scan"
    if bundled.exists():
        bundled.chmod(bundled.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return str(bundled)

    if found := shutil.which("netscope-scan"):
        return found

    raise RuntimeError(
        "netscope-scan binary not found. "
        "Install it or set NETSCOPE_BIN=/path/to/netscope-scan"
    )


def _args(
    addresses: list[str],
    *,
    ports: list[int] | None,
    range: tuple[int, int] | None,
    batch_size: int,
    timeout: int,
    tries: int,
    ulimit: int | None,
    scan_order: str,
    top: bool,
    exclude_ports: list[int] | None,
    exclude_addresses: list[str] | None,
    udp: bool,
    resolver: str | None,
) -> list[str]:
    """Build the full argv list for a netscope-scan invocation.

    Port selection is mutually exclusive: *ports*, *range*, and *top* are
    evaluated in that priority order — the first truthy value wins.

    Args:
        addresses: Target IPs, CIDRs, or hostnames. Passed as a single
            comma-joined ``-a`` value.
        ports: Explicit port list (``-p``). Takes priority over *range* and
            *top* when provided.
        range: Port range as ``(start, end)`` inclusive (``-r``). Used when
            *ports* is ``None``.
        batch_size: Concurrent socket count (``-b``).
        timeout: Per-port connection timeout in milliseconds (``-t``).
        tries: Number of probe attempts per port (``--tries``).
        ulimit: File-descriptor limit to request from the OS (``-u``,
            Unix only). Skipped when ``None``.
        scan_order: ``"serial"`` or ``"random"`` (``--scan-order``).
        top: When ``True`` and neither *ports* nor *range* is set, passes
            ``--top`` to scan the 1 000 most common ports.
        exclude_ports: Port numbers to skip (``-e``).
        exclude_addresses: Addresses or CIDRs to exclude (``-x``).
        udp: When ``True``, enables UDP mode (``--udp``).
        resolver: Comma-separated custom DNS resolver addresses
            (``--resolver``). Skipped when ``None``.

    Returns:
        A list of strings suitable as the first argument to
        :func:`subprocess.run` or :func:`asyncio.create_subprocess_exec`.
    """
    cmd = [_binary(), "--no-config", "-a", ",".join(addresses)]

    if ports:
        cmd += ["-p", ",".join(map(str, ports))]
    elif range is not None:
        cmd += ["-r", f"{range[0]}-{range[1]}"]
    elif top:
        cmd += ["--top"]

    cmd += ["-b", str(batch_size), "-t", str(timeout), "--tries", str(tries)]
    cmd += ["--scan-order", scan_order]

    if ulimit is not None:
        cmd += ["-u", str(ulimit)]
    if exclude_ports:
        cmd += ["-e", ",".join(map(str, exclude_ports))]
    if exclude_addresses:
        cmd += ["-x", ",".join(exclude_addresses)]
    if udp:
        cmd += ["--udp"]
    if resolver:
        cmd += ["--resolver", resolver]

    return cmd


def _parse(raw: bytes) -> list[ScanResult]:
    """Deserialise raw JSON stdout from netscope-scan.

    The binary emits a JSON array where each element has the shape::

        {"ip": "<address>", "ports": [<int>, ...]}

    Only hosts with at least one open port are included.

    Args:
        raw: Raw bytes captured from the binary's stdout.

    Returns:
        List of :class:`~netscope.ScanResult` instances.
    """
    return [ScanResult(ip=r["ip"], ports=r["ports"]) for r in json.loads(raw)]


def scan(
    addresses: list[str],
    *,
    ports: list[int] | None = None,
    range: tuple[int, int] | None = None,
    batch_size: int = 4500,
    timeout: int = 1500,
    tries: int = 1,
    ulimit: int | None = None,
    scan_order: str = "serial",
    top: bool = False,
    exclude_ports: list[int] | None = None,
    exclude_addresses: list[str] | None = None,
    udp: bool = False,
    resolver: str | None = None,
) -> list[ScanResult]:
    """Run a blocking port scan via netscope-scan.

    Spawns the binary with :func:`subprocess.run`, blocks until it exits,
    and returns the parsed results. For non-blocking execution use
    :func:`scan_async`.

    Args:
        addresses: One or more targets — IPs, CIDRs (e.g. ``"10.0.0.0/24"``),
            or hostnames.
        ports: Explicit port numbers to probe. Mutually exclusive with *range*
            and *top* (first non-``None`` value wins).
        range: Port range as ``(start, end)`` inclusive, e.g. ``(1, 1000)``.
        batch_size: Maximum number of concurrent in-flight sockets.
            Defaults to ``4500``.
        timeout: Per-port connection timeout in milliseconds. Defaults to
            ``1500``.
        tries: Number of probe retries per port. Defaults to ``1``.
        ulimit: File-descriptor limit to request from the OS (Unix only).
            Useful when *batch_size* exceeds the default ``ulimit -n``.
        scan_order: Probe order — ``"serial"`` (default) scans ports in
            ascending order; ``"random"`` shuffles them.
        top: Scan the 1 000 most common ports. Ignored when *ports* or
            *range* is provided.
        exclude_ports: Port numbers to skip entirely.
        exclude_addresses: IPs or CIDRs to remove from the target set.
        udp: Enable UDP scanning (TCP by default).
        resolver: Comma-separated custom DNS resolver addresses used for
            hostname resolution.

    Returns:
        List of :class:`~netscope.ScanResult` — one entry per reachable host.
        Hosts with no open ports are omitted.

    Raises:
        RuntimeError: If the netscope-scan binary cannot be located.
        ScanError: If the binary exits with a non-zero return code.

    Example::

        from netscope import scan

        results = scan(
            ["192.168.1.0/24"],
            ports=[22, 80, 443],
            timeout=2000,
        )
        for r in results:
            print(r.ip, r.ports)
    """
    cmd = _args(
        addresses, ports=ports, range=range, batch_size=batch_size,
        timeout=timeout, tries=tries, ulimit=ulimit, scan_order=scan_order,
        top=top, exclude_ports=exclude_ports, exclude_addresses=exclude_addresses,
        udp=udp, resolver=resolver,
    )
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise ScanError(result.stderr.decode().strip())
    return _parse(result.stdout)


async def scan_async(
    addresses: list[str],
    *,
    ports: list[int] | None = None,
    range: tuple[int, int] | None = None,
    batch_size: int = 4500,
    timeout: int = 1500,
    tries: int = 1,
    ulimit: int | None = None,
    scan_order: str = "serial",
    top: bool = False,
    exclude_ports: list[int] | None = None,
    exclude_addresses: list[str] | None = None,
    udp: bool = False,
    resolver: str | None = None,
) -> list[ScanResult]:
    """Run a non-blocking port scan via netscope-scan.

    Spawns the binary with :func:`asyncio.create_subprocess_exec` so the
    event loop remains free while the scan runs. Accepts the same arguments
    as :func:`scan`.

    Args:
        addresses: One or more targets — IPs, CIDRs, or hostnames.
        ports: Explicit port numbers to probe.
        range: Port range as ``(start, end)`` inclusive.
        batch_size: Maximum concurrent in-flight sockets. Defaults to ``4500``.
        timeout: Per-port connection timeout in milliseconds. Defaults to
            ``1500``.
        tries: Probe retries per port. Defaults to ``1``.
        ulimit: File-descriptor limit to request from the OS (Unix only).
        scan_order: ``"serial"`` (default) or ``"random"``.
        top: Scan the 1 000 most common ports.
        exclude_ports: Port numbers to skip.
        exclude_addresses: IPs or CIDRs to exclude.
        udp: Enable UDP scanning.
        resolver: Custom DNS resolver addresses (comma-separated string).

    Returns:
        List of :class:`~netscope.ScanResult` — one entry per reachable host.

    Raises:
        RuntimeError: If the netscope-scan binary cannot be located.
        ScanError: If the binary exits with a non-zero return code.

    Example::

        import asyncio
        from netscope import scan_async

        async def main() -> None:
            results = await scan_async(["10.0.0.1"], range=(1, 65535))
            for r in results:
                print(r.ip, r.ports)

        asyncio.run(main())
    """
    cmd = _args(
        addresses, ports=ports, range=range, batch_size=batch_size,
        timeout=timeout, tries=tries, ulimit=ulimit, scan_order=scan_order,
        top=top, exclude_ports=exclude_ports, exclude_addresses=exclude_addresses,
        udp=udp, resolver=resolver,
    )
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise ScanError(stderr.decode().strip())
    return _parse(stdout)
