from datetime import UTC, datetime, timedelta
from os import environ
from typing import Any

from pydantic import ValidationError
from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Collapsible, Label, Link, ListItem, ListView, MarkdownViewer

from github_feed.app import get_db_client
from github_feed.github_client import GitHubClient
from github_feed.models import Release
from github_feed.utils import extract_repo_name_from_html_url


class ReleasesList(Widget):
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
        """Called when the input changes"""
        self.log.info("CLICK CLICK CLICK :D")
        self.update_releases()

    @work(exclusive=True)
    async def update_releases(self) -> None:
        recently_updated = self.db.get_updated_repos(datetime.now(UTC) - timedelta(hours=8))
        token = environ["GITHUB_TOKEN"]
        client = GitHubClient(token)
        releases: list[Release] = []
        # Iterate over recently updated repos and check for new releases
        for repo in recently_updated:
            self.log.info(f"Checking for new releases for repo: {repo.name}")
            try:
                latest_release = client.get_latest_release(repo.releases_url)
                if latest_release.created_at > datetime.now(UTC) - timedelta(days=7):
                    releases.append(latest_release)
            except ValidationError:
                self.log.warning(f"Error validating release: {repo.name}")
            pass
        # TODO: Use releases to update the ListView
        releases_list: ListView = self.query_one("#releasesList", ListView)
        self.log.info(f"Found {len(releases)} new releases")
        self.log.info(f"{releases_list=}")
        self.log.info(f"{releases_list.children=}")
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
