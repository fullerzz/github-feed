from os import environ
from typing import Any, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Label, DataTable, Link

from github_feed.app import get_db_client, populate_table, retrieve_activity
from github_feed.components.env_var_panel import EnvVarPanel
from github_feed.components.metadata_panel import MetadataPanel
from github_feed.components.releases_list import ReleasesList
from github_feed.models import Repository


class Home(Screen):  # type: ignore[type-arg]
    BINDINGS: ClassVar = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                EnvVarPanel(shrink=True, id="envVarPanel"),
                MetadataPanel(323, id="metadataPanel"),
                classes="row",
            ),
            Horizontal(
                Button("Check for New Releases", id="checkReleases", variant="primary"),
                Button("Refresh List of Starred Repos", id="checkStarred", variant="error"),
                classes="row",
            ),
        )


class Releases(Screen):  # type: ignore[type-arg]
    BINDINGS: ClassVar = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(ReleasesList())


class StarredRepos(Screen):  # type: ignore[type-arg]
    BINDINGS: ClassVar = [("escape", "app.pop_screen", "Pop screen")]

    def __init__(self, **kwargs: Any) -> None:
        self.db = get_db_client()
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(Label("Starred Repos"), DataTable(zebra_stripes=True, id="starredRepos"))

    async def on_mount(self) -> None:
        # TODO: Retrieve starred repos
        self.log.info("Retrieving starred repos")
        self.populate_initial_table()

    @work(exclusive=True)
    async def populate_initial_table(self) -> None:
        starred_repos = self.db.get_starred_repos()
        self.notify(f"Retrieved {len(starred_repos)} starred repos from the database")
        table = self.query_one("#starredRepos", DataTable)
        table.add_columns("Name", "Link", "Language", "Stargazers", "Updated At", "Description")
        for repo in starred_repos:
            table.add_row(
                repo.name,
                f"[link]{repo.html_url}[/link]",
                repo.language,
                repo.stargazers_count,
                repo.updated_at,
                repo.description,
            )

    @work(exclusive=True)
    async def refresh_starred_repos(self) -> None:
        # TODO: Add way to invoke this method
        starred_repos = retrieve_activity()
        populate_table(starred_repos, self.db)
        # TODO: Update this to initially populate the DataTable with values from the db
        # Then, update the DataTable with the results from the API call
        await self.populate_data_table(starred_repos)

    async def populate_data_table(self, starred_repos: list[Repository]) -> None:
        table = self.query_one("#starredRepos", DataTable)
        table.add_columns("Name", "Description", "Link", "Homepage", "Language", "Stargazers", "Updated At")
        for repo in starred_repos:
            table.add_row(
                repo.name,
                repo.description,
                repo.html_url,
                repo.homepage,
                repo.language,
                repo.stargazers_count,
                repo.updated_at,
            )


class GitHubFeed(App[str]):
    CSS_PATH = "css/tui.tcss"
    BINDINGS: ClassVar = [
        ("b", "push_screen('home')", "HOME"),
        ("c", "push_screen('releases')", "RELEASES"),
        ("s", "push_screen('starred_repos')", "STARRED REPOS"),
    ]

    def on_mount(self) -> None:
        self.install_screen(Home(), name="home")
        self.install_screen(Releases(), name="releases")
        self.install_screen(StarredRepos(), name="starred_repos")
        self.push_screen("home")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "checkReleases":
            self.notify("Check releases button pressed!")
        elif button_id == "checkStarred":
            self.notify("Check starred button pressed!")


if __name__ == "__main__":
    app = GitHubFeed()
    app.run()
