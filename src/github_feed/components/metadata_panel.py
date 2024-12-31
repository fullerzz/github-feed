from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from textual import on, work
from textual.events import Show
from textual.widgets import Static
from textual.worker import get_current_worker

from github_feed.engine import Engine


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
    def __init__(
        self, engine: Engine, starred_repo_count: int, last_checked: datetime | None = None, **kwargs: Any
    ) -> None:
        self.engine = engine
        self.starred_repo_count = starred_repo_count
        self.last_checked = last_checked
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        panel_parts = build_panel_parts(self.starred_repo_count, self.last_checked)
        panel = Panel(panel_parts.body, title=panel_parts.title, expand=False, padding=(1, 1))
        self.update(panel)

    @on(Show)
    def handle_screen_resume(self) -> None:
        self.load_metadata()

    @work(exclusive=True, thread=True)
    def load_metadata(self) -> None:
        worker = get_current_worker()
        if not worker.is_cancelled:
            starred_repos_count = len(self.engine.retrieve_starred_repos())
            last_checked = datetime.now()
            panel_parts = build_panel_parts(starred_repos_count, last_checked)
            panel = Panel(panel_parts.body, title=panel_parts.title, expand=False, padding=(1, 1))
            self.app.call_from_thread(self.update, panel)
