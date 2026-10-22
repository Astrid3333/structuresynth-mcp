"""Minimal TCP bridge to a running Unreal Engine instance (port 55557).

Speaks the same JSON protocol as the user's unreal-mcp server:
    send:  {"type": "<command>", "params": {...}}
    recv:  one JSON object (may be chunked over TCP).
"""

from __future__ import annotations

import json
import socket

UNREAL_HOST = "127.0.0.1"
UNREAL_PORT = 55557
_TIMEOUT = 30
_JSON_MAY_END = b"} \t\r\n"


class UnrealNotRunning(RuntimeError):
    pass


def _recv_full(sock: socket.socket) -> bytes:
    buf = bytearray()
    sock.settimeout(_TIMEOUT)
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            if not buf:
                raise ConnectionError("Unreal closed the connection before responding.")
            raise ConnectionError(
                f"Unreal closed with incomplete response ({len(buf)} bytes)."
            )
        buf.extend(chunk)
        if buf[-1] not in _JSON_MAY_END:
            continue
        try:
            json.loads(bytes(buf).decode("utf-8"))
            return bytes(buf)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue


def send_command(command: str, params: dict | None = None, timeout: int = _TIMEOUT) -> dict:
    """Send one command to Unreal and return the parsed JSON response."""
    payload = json.dumps({"type": command, "params": params or {}}).encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((UNREAL_HOST, UNREAL_PORT))
        sock.sendall(payload)
        raw = _recv_full(sock)
    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        raise UnrealNotRunning(
            f"Cannot reach Unreal at {UNREAL_HOST}:{UNREAL_PORT} "
            f"({e}). Is the editor running with the MCP plugin?"
        ) from e
    finally:
        sock.close()
    return json.loads(raw.decode("utf-8"))


def import_asset(source_path: str, dest_path: str = "/Game/Imported",
                 name: str = "", replace: bool = True) -> dict:
    """Import a file on disk into Unreal's content browser via the bridge."""
    return send_command("import_asset", {
        "source_path": str(source_path),
        "path": str(dest_path),
        "name": str(name),
        "replace": bool(replace),
    })
