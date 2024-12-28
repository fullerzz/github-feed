from rich.box import HEAVY
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from github_feed import utils
from github_feed.models import Release

console = Console()

RELEASE_COLUMNS = ["html_url", "tag_name", "created_at"]


def _build_row(release: Release) -> list[str]:
    data = release.model_dump()
    return [str(data[column]) for column in RELEASE_COLUMNS]


def display_releases(releases: list[Release]) -> None:
    table = Table(title="New Releases")
    for field_name in RELEASE_COLUMNS:
        table.add_column(field_name)

    for release in releases:
        table.add_row(*_build_row(release))

    console.print(table)


def display_releases_panels(releases: list[Release]) -> None:
    for release in releases:
        repo_name = utils.extract_repo_name_from_html_url(release.html_url)
        title = f"[bold cyan]{repo_name}[/bold cyan] - [bold green]{release.tag_name}[/]"
        console.print(
            Panel(
                Markdown(release.body, code_theme="one-dark", justify="left"),
                box=HEAVY,
                title=title,
                expand=False,
                highlight=True,
                padding=(0, 2),
            ),
            new_line_start=True,
        )
