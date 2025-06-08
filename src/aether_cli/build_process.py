from pathlib import Path

from aether import render
from bs4 import BeautifulSoup
from rich.console import Console

from .utils import load_build_function_instance


def _update_paths_in_soup(
    console: Console,
    soup: BeautifulSoup,
    prefix: str,
    static_assets_dir: Path,
    static_css_dir: Path,
    static_js_dir: Path,
    output_dir: Path,
    verbose: bool = False,
) -> BeautifulSoup:
    if verbose:
        console.print("Updating paths in HTML...")

    # Update link, img, script & a tags
    for tag_name, attribute in [
        ("link", "href"),
        ("img", "src"),
        ("script", "src"),
        ("a", "href"),
    ]:
        for tag in soup.find_all(tag_name):
            if attribute in tag.attrs:
                if not tag[attribute].startswith(("http://", "https://", "/")):
                    old_path = Path(tag[attribute])
                    if Path("styles") in old_path.parents:
                        new_path = static_css_dir / old_path.relative_to("styles")
                    elif Path("js_scripts") in old_path.parents:
                        new_path = static_js_dir / old_path.relative_to("js_scripts")
                    elif Path("assets") in old_path.parents:
                        new_path = static_assets_dir / old_path.relative_to("assets")
                    elif Path("public") in old_path.parents:
                        new_path = output_dir / old_path.relative_to("public")
                    else:
                        # Note: Need to find a better way to handle pages condition. Right now, we are just shoving it in this else block.
                        # Note: Assuming the stem in href is same as the page_name mentioned in the config.
                        if ".html" in old_path.name:
                            new_path = output_dir / old_path.relative_to(".")
                        else:
                            new_path = output_dir / old_path.name

                    new_path = new_path.relative_to(output_dir)
                    if prefix:
                        new_path = prefix / new_path

                    if verbose:
                        console.print(
                            f"Updating {attribute}: {old_path} -> /{new_path}"
                        )
                    tag[attribute] = f"/{new_path}"

    return soup


def builder(
    console: Console,
    output_html_file_name: str,
    output_dir: Path,
    prefix: str,
    file_target: Path,
    function_target: str,
    static_assets_dir: Path,
    static_css_dir: Path,
    static_js_dir: Path,
    verbose: bool = False,
) -> None:
    if verbose:
        console.print(
            f"Loading build function instance for '{output_html_file_name}.html'..."
        )
    instance = load_build_function_instance(file_target, function_target)

    if verbose:
        console.print("Rendering HTML...")

    rendered_html = render(instance())
    soup = BeautifulSoup(rendered_html, "html.parser")
    updated_soup = _update_paths_in_soup(
        console=console,
        soup=soup,
        prefix=prefix,
        output_dir=output_dir,
        static_assets_dir=static_assets_dir,
        static_css_dir=static_css_dir,
        static_js_dir=static_js_dir,
        verbose=verbose,
    )

    output_html_path = output_dir / output_html_file_name
    if not output_html_path.parent.exists():
        if verbose:
            console.print(f"Creating routing directory: {output_html_path.parent}")

        output_html_path.parent.mkdir(parents=True)

    if verbose:
        console.print("Writing final HTML to file...")

    with open(output_html_path, "w", encoding="utf-8") as file:
        file.write(updated_soup.decode(pretty_print=True, formatter="html5"))
