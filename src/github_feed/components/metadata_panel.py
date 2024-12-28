from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from textual.widgets import Static


class PanelParts(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    body: RenderableType


def _build_starred_repos_line(repo_count: int) -> str:
    line = f"🌟 [bold cyan]Starred Repository Count[/]: [bold green]{repo_count!s}[/]"
    return line


def _build_last_checked_line(timestamp: datetime | None) -> str:
    if timestamp is None:
        line = "⌚ [bold cyan]Last Checked[/]: [bold red]Never[/]"
    else:
        line = f"⌚ [bold cyan]Last Checked[/]: [bold green]{timestamp.isoformat()}[/]"
    return line


def _build_body(starred_count: int, last_checked: datetime | None) -> RenderableType:
    line_1 = _build_starred_repos_line(starred_count)
    line_2 = _build_last_checked_line(last_checked)
    body_lines = "\n".join([line_1, "", line_2])
    return Align.center(body_lines)


def build_panel_parts(starred_count: int, last_checked: datetime | None) -> PanelParts:
    return PanelParts(title="Metadata", body=_build_body(starred_count, last_checked))


class MetadataPanel(Static):
    def __init__(self, starred_repo_count: int, last_checked: datetime | None = None, **kwargs: Any) -> None:
        self.starred_repo_count = starred_repo_count
        self.last_checked = last_checked
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        panel_parts = build_panel_parts(self.starred_repo_count, self.last_checked)
        panel = Panel(panel_parts.body, title=panel_parts.title, expand=False, padding=(1, 1))
        self.update(panel)
