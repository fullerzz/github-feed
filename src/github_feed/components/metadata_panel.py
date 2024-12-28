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


def _build_starred_repos_line() -> str:
    line = "🌟 [bold cyan]Starred Repository Count[/]:"

    return line


def _build_last_checked_line() -> str:
    line = "⌚ [bold cyan]Last Checked[/]:"
    return line


def _build_body() -> RenderableType:
    line_1 = _build_starred_repos_line()
    line_2 = _build_last_checked_line()
    body_lines = "\n".join([line_1, "", line_2])
    return Align.center(body_lines)


def build_panel_parts() -> PanelParts:
    return PanelParts(title="Metadata", body=_build_body())


class MetadataPanel(Static):
    def on_mount(self) -> None:
        panel_parts = build_panel_parts()
        panel = Panel(panel_parts.body, title=panel_parts.title, expand=False, padding=(1, 1))
        self.update(panel)
