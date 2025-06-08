from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import]


class BuildConfig(BaseModel):
    index_page_file_target: Path
    index_page_function_target: str

    output_dir: Path

    pages_file_targets: list[Path]
    pages_function_targets: list[str]
    pages_names: list[str]

    @model_validator(mode="after")
    def validate_attrs(self) -> Self:
        if len(self.pages_file_targets) != len(self.pages_function_targets):
            raise ValueError(
                "Each 'pages_file_target' must have a corresponding 'pages_function_target'."
            )
        if len(self.pages_file_targets) != len(self.pages_names):
            raise ValueError(
                "Each 'pages_file_target' must have a corresponding 'pages_name'."
            )

        return self


class RunConfig(BaseModel):
    host: str | None
    port: int


class StaticContentConfig(BaseModel):
    assets_dir: Path | None
    js_scripts_dir: Path | None
    public_dir: Path | None
    styles_dir: Path | None


class Config(BaseModel):
    build_config: BuildConfig
    components_dir: Path
    run_config: RunConfig
    static_content_config: StaticContentConfig


def load_configs() -> Config:
    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        raise FileNotFoundError("Unable to locate configuration file.")

    with open(pyproject_file, "rb") as file:
        raw_aether_config: dict = tomllib.load(file).get("tool", {}).get("aether", {})

        raw_aether_build_config: dict = raw_aether_config.get("build", {})
        raw_aether_components_dir: str = raw_aether_config.get(
            "components_dir", "ui/components/"
        )
        raw_aether_run_config: dict = raw_aether_config.get("run", {})
        raw_aether_static_content_config: dict = raw_aether_config.get(
            "static_content", {}
        )

    # Decompose raw 'build' configurations.
    # TODO: Add fallbacks/defaults if the lengths of file_targets and function_targets are different
    parsed_build_config = BuildConfig(
        index_page_file_target=raw_aether_build_config.get("index_page", {}).get(
            "file_target", "main.py"
        ),
        index_page_function_target=raw_aether_build_config.get("index_page", {}).get(
            "function_target", "main"
        ),
        output_dir=raw_aether_build_config.get("output_dir", "build/"),
        pages_file_targets=raw_aether_build_config.get("pages", {}).get(
            "file_targets", []
        ),
        pages_function_targets=raw_aether_build_config.get("pages", {}).get(
            "function_targets", []
        ),
        pages_names=raw_aether_build_config.get("pages", {}).get("names", []),
    )

    parsed_components_dir = Path(raw_aether_components_dir)

    # Decompose raw 'run' configurations.
    parsed_run_config = RunConfig(
        host=raw_aether_run_config.get("host", None),
        port=raw_aether_run_config.get("port", 8080),
    )

    # Decompose raw 'static content' configurations.
    parsed_static_content_config = StaticContentConfig(
        assets_dir=raw_aether_static_content_config.get("assets_dir"),
        js_scripts_dir=raw_aether_static_content_config.get("js_scripts_dir"),
        public_dir=raw_aether_static_content_config.get("public_dir"),
        styles_dir=raw_aether_static_content_config.get("styles_dir"),
    )

    return Config(
        build_config=parsed_build_config,
        components_dir=parsed_components_dir,
        run_config=parsed_run_config,
        static_content_config=parsed_static_content_config,
    )


configs = load_configs()
