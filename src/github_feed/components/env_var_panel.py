import os

from pydantic import BaseModel, ConfigDict
from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from textual.widgets import Static


class PanelParts(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    body: RenderableType


def _build_github_token_line() -> str:
    github_token_line = "[bold]$GITHUB_TOKEN[/]:"  # noqa: S105
    if os.getenv("GITHUB_TOKEN") is None:
        github_token_line += " [red italic]Missing[/] ❌"
    else:
        github_token_line += " [green]Present[/] ✔️"
    return github_token_line


def _build_db_filename_line() -> str:
    db_filename_line = "[bold]$DB_FILENAME[/]:"
    if os.getenv("DB_FILENAME") is None:
        db_filename_line += " [yellow italic]Missing[/] ⚠️ Using default..."
    else:
        db_filename_line += " [green]Present[/] ✔️"
    return db_filename_line


def _build_body() -> RenderableType:
    line_1 = _build_github_token_line()
    line_2 = _build_db_filename_line()
    body_lines = "\n".join([line_1, "", line_2])
    return Align.center(body_lines)


def build_panel_parts() -> PanelParts:
    return PanelParts(title="Environment Variables Present?", body=_build_body())


class EnvVarPanel(Static):
    def on_mount(self) -> None:
        panel_parts = build_panel_parts()
        panel = Panel(panel_parts.body, title=panel_parts.title, expand=False, padding=(1, 1))
        self.update(panel)
