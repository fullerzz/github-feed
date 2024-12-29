from datetime import UTC, datetime, timedelta
from os import environ
from typing import Any

from pydantic import ValidationError
from textual import on, work
from textual.app import ComposeResult
from textual.events import Show
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Collapsible, Label, Link, ListItem, ListView, MarkdownViewer
from textual.worker import get_current_worker

from github_feed.app import get_db_client
from github_feed.github_client import GitHubClient
from github_feed.models import Release
from github_feed.utils import extract_repo_name_from_html_url


class ReleasesList(Widget):
    class DataLoaded(Message):
        def __init__(self, loaded: bool) -> None:
            self.loaded = loaded
            super().__init__()

    def __init__(self, **kwargs: Any) -> None:
        self.db = get_db_client()
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield ListView(
            ListItem(Collapsible(Label("Nested content for Zach"), title="Zach")),
            ListItem(Collapsible(Label("Nested content for Nicole"), title="Nicole")),
            id="releasesList",
            name="releasesList",
        )

    async def on_mount(self) -> None:
        list_view = self.query_one("#releasesList", ListView)
        list_view.loading = True

    @on(Show)
    def handle_screen_resume(self) -> None:
        self.update_releases()

    @work(exclusive=True, thread=True)
    def update_releases(self) -> None:
        worker = get_current_worker()
        recently_updated = self.db.get_updated_repos(datetime.now(UTC) - timedelta(hours=48))
        token = environ["GITHUB_TOKEN"]
        client = GitHubClient(token)
        releases: list[Release] = []
        if not worker.is_cancelled:
            # Iterate over recently updated repos and check for new releases
            for repo in recently_updated:
                self.log.info(f"Checking for new releases for repo: {repo.name}")
                try:
                    latest_release = client.get_latest_release(repo.releases_url)
                    if latest_release.created_at > datetime.now(UTC) - timedelta(days=7):
                        releases.append(latest_release)
                except ValidationError:
                    self.log.warning(f"Error validating release: {repo.name}")
        self.rebuild_table(releases=releases)

    @work(exclusive=True)
    async def rebuild_table(self, releases: list[Release]) -> None:
        releases_list = self.query_one("#releasesList", ListView)

        releases_list.clear()
        self.log.info(f"After clearing: {releases_list=}")
        for release in releases:
            repo_name = extract_repo_name_from_html_url(release.html_url)
            title = f"[bold]{repo_name}[/bold] - {release.tag_name}"
            releases_list.append(
                ListItem(
                    Collapsible(
                        Link(release.html_url, url=release.html_url, tooltip="View release on GitHub"),
                        MarkdownViewer(release.body),
                        title=title,
                    )
                )
            )
        releases_list.loading = False
        self.post_message(self.DataLoaded(loaded=True))
