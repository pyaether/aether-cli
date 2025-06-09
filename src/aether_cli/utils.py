import importlib
import importlib.util
import socket
import sys
from pathlib import Path
from typing import Any


class ImportFromStringError(Exception):
    pass


def load_build_function_instance(file_target: str, function_target: str) -> Any:
    working_dir = Path.cwd()
    working_file = Path(file_target)

    if not working_file.exists():
        raise FileNotFoundError(f"File '{file_target}' not found.")

    module_path = working_dir / file_target
    module_name = Path(file_target).stem

    sys.path.append(str(working_dir))

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        raise ImportFromStringError(
            f"Could not import module from path '{module_path}'"
        )

    try:
        instance = getattr(module, function_target)
    except AttributeError:
        message = f'Attribute "{function_target}" not found in module "{module_name}".'
        raise ImportFromStringError(message)

    return instance


def get_local_ip():
    """Tries to find the local network IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None
