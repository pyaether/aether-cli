import http.server
import socketserver
from datetime import datetime
from pathlib import Path

from rich.console import Console


def request_handler(console: Console, directory_path: str):
    class RichHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory_path, **kwargs)

        def log_message(self, format, *args):
            status_code = args[1]
            request_line = args[0]

            if status_code.startswith("2"):
                status_color = "green"
            elif status_code.startswith("3"):
                status_color = "yellow"
            else:
                status_color = "red"

            timestamp = f"[[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]]"

            console.print(
                f"{timestamp} INFO:\t"
                f'{self.address_string()} - "{request_line}" '
                f"[{status_color}]{status_code}[/{status_color}]"
            )

    return RichHTTPRequestHandler


def tcp_server(
    console: Console, host: str | None, port: int, directory_path: Path
) -> socketserver.TCPServer:
    handler_factory = request_handler(console, str(directory_path))

    if host is None:
        host = ""

    return socketserver.TCPServer((host, port), handler_factory)
