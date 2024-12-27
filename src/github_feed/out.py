from rich.console import Console
from rich.table import Table

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
