import shutil
import signal
import threading
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from . import __version__
from .build_process import builder
from .configs import configs
from .run_server import tcp_server
from .utils import get_local_ip


@click.group()
def main() -> None:
    pass


@main.command()
def version():
    console = Console()
    console.print(f"Aether CLI version: [green]{__version__}[/green]")


@main.command()
@click.option(
    "--prefix",
    type=str,
    default="",
    help="Inject 'base_path' prefix in the generated HTML file.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose mode to echo steps.")
def build(prefix: str, verbose: bool) -> None:
    console = Console()

    def _create_dir_if_not_exists(directory: Path) -> None:
        if not directory.exists():
            if verbose:
                console.print(f"Creating directory: {directory}")
            directory.mkdir(parents=True)

    _create_dir_if_not_exists(configs.build_config.output_dir)

    static_dir = configs.build_config.output_dir / "static"
    # _create_dir_if_not_exists(configs.build_config.output_dir)

    static_css_dir = static_dir / "css"
    _create_dir_if_not_exists(static_css_dir)

    static_js_dir = static_dir / "js"
    _create_dir_if_not_exists(static_js_dir)

    static_assets_dir = static_dir / "assets"
    _create_dir_if_not_exists(static_assets_dir)

    def _copy_dir(src: Path | None, dest: Path, directory_name: str) -> None:
        if src and src.exists():
            if verbose:
                console.print(f"Copying {directory_name} from {src} to {dest}")
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            console.print(f"Project doesn't have a '{directory_name}' directory.")

    _copy_dir(configs.static_content_config.assets_dir, static_assets_dir, "assets")
    _copy_dir(configs.static_content_config.styles_dir, static_css_dir, "styles")
    _copy_dir(configs.static_content_config.js_scripts_dir, static_js_dir, "js_scripts")
    _copy_dir(
        configs.static_content_config.public_dir,
        configs.build_config.output_dir,
        "public",
    )

    if verbose:
        console.print("Building Index HTML...")

    builder(
        console=console,
        output_html_file_name="index.html",
        output_dir=configs.build_config.output_dir,
        prefix=prefix,
        file_target=configs.build_config.index_page_file_target,
        function_target=configs.build_config.index_page_function_target,
        static_assets_dir=static_assets_dir,
        static_css_dir=static_css_dir,
        static_js_dir=static_js_dir,
        verbose=verbose,
    )

    if configs.build_config.pages_file_targets:
        if verbose:
            console.print("Building Pages...")

        for file_target, function_target, page_name in zip(
            configs.build_config.pages_file_targets,
            configs.build_config.pages_function_targets,
            configs.build_config.pages_names,
            strict=False,
        ):
            builder(
                console=console,
                output_html_file_name=f"{page_name}.html",
                output_dir=configs.build_config.output_dir,
                prefix=prefix,
                file_target=file_target,
                function_target=function_target,
                static_assets_dir=static_assets_dir,
                static_css_dir=static_css_dir,
                static_js_dir=static_js_dir,
                verbose=verbose,
            )

    console.print("\n[bold green]Build successful![/bold green]")


@main.command()
def run() -> None:
    console = Console()
    interrupt_event = threading.Event()

    if not configs.build_config.output_dir.exists():
        console.print("[bold red]Build directory not found.[/bold red]")
        console.print("Please run 'pytempl-cli build' first.")
        return

    try:
        server = tcp_server(
            console=console,
            host=configs.run_config.host,
            port=configs.run_config.port,
            directory_path=configs.build_config.output_dir,
        )
    except OSError:
        console.print(
            f"[bold red]Error: Could not bind to address http://{configs.run_config.host if configs.run_config.host is not None else '127.0.0.1'}:{configs.run_config.port}.[/bold red]"
        )
        console.print(f"Is port {configs.run_config.port} already in use?")
        return

    def shutdown_handler(signum, _frame):
        """Gracefully shut down the server."""
        signal_name = signal.Signals(signum).name
        console.print(
            f"\n[bold yellow]Received {signal_name}. Shutting down server...[/bold yellow]"
        )

        server.shutdown()
        interrupt_event.set()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    with Live(
        Spinner("dots", text=" Starting server..."), console=console, transient=True
    ):
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column()
    info_table.add_column()

    info_table.add_row("✓", "[bold green]Aether App[/bold green] is running!")
    info_table.add_row(
        "  ",
        f"[cyan]Local:[/cyan]      http://{configs.run_config.host if configs.run_config.host is not None else '127.0.0.1'}:{configs.run_config.port}",
    )

    local_ip = get_local_ip()
    if local_ip:
        info_table.add_row(
            "  ",
            f"[cyan]Network:[/cyan]    http://{local_ip}:{configs.run_config.port}",
        )

    console.print(info_table)
    console.print("\nPress CTRL+C to stop the server.\n")

    try:
        interrupt_event.wait()
    finally:
        console.print("[bold red]Server has been shut down.[/bold red]")
        signal.signal(signal.SIGINT, signal.getsignal(signal.SIGINT))
        signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGTERM))


if __name__ == "__main__":
    main()
