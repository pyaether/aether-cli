import click
from rich.console import Console

from . import __version__


@click.group()
def main() -> None:
    pass


@main.command()
def version():
    console = Console()
    console.print(f"Aether CLI version: [green]{__version__}[/green]")
