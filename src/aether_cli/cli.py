import shutil
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .build_process import builder
from .configs import configs


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
            console.print(f"Project doesn't have a '{src}' directory.")

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
