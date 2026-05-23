"""Data models and exceptions for the netscope package."""

from dataclasses import dataclass


@dataclass
class ScanResult:
    """A single host entry returned by netscope-scan.

    Only hosts with at least one open port appear in the binary's output,
    so ``ports`` is always non-empty.

    Attributes:
        ip: The IP address of the scanned host as a dotted-decimal string
            (e.g. ``"192.168.1.1"``).
        ports: List of open port numbers discovered on this host.

    Example::

        result = ScanResult(ip="10.0.0.1", ports=[22, 80, 443])
        print(result.ip)     # "10.0.0.1"
        print(result.ports)  # [22, 80, 443]
    """

    ip: str
    ports: list[int]


class ScanError(RuntimeError):
    """Raised when netscope-scan exits with a non-zero return code.

    Inherits from :exc:`RuntimeError` so callers that only catch broad
    runtime errors will still see the failure.

    Example::

        try:
            scan(["256.256.256.256"])
        except ScanError as e:
            print(e)  # human-readable message with stderr output
    """
