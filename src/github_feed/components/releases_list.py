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

JESSICA = """
# Lady Jessica

Bene Gesserit and concubine of Leto, and mother of Paul and Alia.
"""

names = ["Paul", "Leto", "Alia", "Ghanima", "Irulan", "Chani", "Stilgar", "Duncan", "Thufir", "Gurney"]


# FIXME: This is a WIP. Currently, struggling to use a worker to update the ListView items
# with results from the GitHub API.
class ReleasesList(Widget):
    def __init__(self, **kwargs: Any) -> None:
        self.db = DbClient(f"sqlite:///{environ['DB_FILENAME']}")
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        items: list[ListItem] = [
            ListItem(Collapsible(Label(f"Nested content for {name}"), title=name)) for name in names
        ]

        yield ListView(
            ListItem(Label("1")),
            ListItem(Label("2")),
            ListItem(Collapsible(Markdown(JESSICA), collapsed=False, title="Jessica")),
            *items,
            id="releasesList",
            name="releasesList",
        )
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
        releases_list: ListView = self.query_one("#releasesList", ListView)  # type: ignore
        self.log.info(f"Found {len(releases)} new releases")
        self.log.info(f"{releases_list=}")
        self.log.info(f"{releases_list.children=}")
        releases_list.clear()
        self.log.info(f"After clearing: {releases_list=}")
        for release in releases:
            releases_list.append(ListItem(Collapsible(Markdown(release.body), title=release.tag_name)))
