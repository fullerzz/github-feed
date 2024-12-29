from datetime import UTC, datetime, timedelta
from os import environ
from typing import Any

from pydantic import ValidationError
from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Collapsible, Label, ListItem, ListView, Markdown

from github_feed.github_client import GitHubClient
from github_feed.models import Release
from github_feed.sql.client import DbClient


class ReleasesList(Widget):
    def __init__(self, **kwargs: Any) -> None:
        self.db = DbClient(f"sqlite:///{environ['DB_FILENAME']}")
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
            releases_list.append(ListItem(Collapsible(Markdown(release.body), title=release.tag_name)))
