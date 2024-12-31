from collections.abc import Sequence
from typing import Any, ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import ScreenResume
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label
from textual.worker import Worker, get_current_worker

from github_feed.components.env_var_panel import EnvVarPanel
from github_feed.components.metadata_panel import MetadataPanel
from github_feed.components.releases_list import ReleasesList
from github_feed.engine import Engine
from github_feed.models import Repository


class Home(Screen):  # type: ignore[type-arg]
    # BINDINGS: ClassVar = [("escape", "app.pop_screen", "Pop screen")]

    def __init__(self, **kwargs: Any) -> None:
        self.engine = Engine()
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Horizontal(
                EnvVarPanel(shrink=True, id="envVarPanel"),
                MetadataPanel(self.engine, 323, id="metadataPanel"),
                classes="row",
            ),
            Horizontal(
                Button("Check for New Releases", id="checkReleases", variant="primary"),
                Button("Refresh List of Starred Repos", id="checkStarred", variant="default"),
                classes="row",
            ),
        )
        yield Footer()


class Releases(Screen):  # type: ignore[type-arg]
    BINDINGS: ClassVar = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(Label("Fresh Releases from GitHub"), ReleasesList())
        yield Footer()

    async def on_mount(self) -> None:
        # Set LoadingIndicator.visible to True
        releases_list = self.query_one(ReleasesList)
        releases_list.loading = True

    @on(ReleasesList.DataLoaded)
    def handle_release_data_loaded(self, event: ReleasesList.DataLoaded) -> None:
        self.log.info(f"{event=}")
        releases_list = self.query_one(ReleasesList)
        releases_list.loading = False


class StarredRepos(Screen):  # type: ignore[type-arg]
    BINDINGS: ClassVar = [("escape", "app.pop_screen", "Pop screen")]

    def __init__(self, **kwargs: Any) -> None:
        self.engine = Engine()
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(Label("Starred Repos"), DataTable(zebra_stripes=True, id="starredRepos"))
        yield Footer()

    async def on_mount(self) -> None:
        # Set DataTable.loading to True
        data_table = self.query_one(DataTable)
        data_table.loading = True

    @on(ScreenResume)
    def handle_screen_resume(self) -> None:
        self.populate_initial_table()

    @work(exclusive=True, thread=True)
    def populate_initial_table(self) -> None:
        worker = get_current_worker()
        starred_repos = self.engine.retrieve_starred_repos()
        data_table = self.query_one(DataTable)
        if not worker.is_cancelled:
            self.app.call_from_thread(self.notify, f"Retrieved {len(starred_repos)} starred repos from the database")
            data_table.add_columns("Name", "Link", "Language", "Stargazers", "Updated At", "Description")
            for repo in starred_repos:
                self.app.call_from_thread(
                    data_table.add_row,
                    repo.name,
                    f"[link]{repo.html_url}[/link]",
                    repo.language,
                    repo.stargazers_count,
                    repo.updated_at,
                    repo.description,
                )
        if not worker.is_cancelled:
            data_table.loading = False
            self.log.info("Updated data table loading state to False")
            self.log.info(f"{data_table=}")

    @work(exclusive=True)
    async def refresh_starred_repos(self) -> None:
        # TODO: Add way to invoke this method
        starred_repos = self.engine.retrieve_starred_repos(refresh=True)
        # TODO: Update this to initially populate the DataTable with values from the db
        # Then, update the DataTable with the results from the API call
        await self.populate_data_table(starred_repos)  # type: ignore # TODO: Fix and remove type-ignore comment

    async def populate_data_table(self, starred_repos: Sequence[Repository]) -> None:
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

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)


class GitHubFeed(App[str]):
    CSS_PATH = "css/tui.tcss"
    BINDINGS: ClassVar = [
        ("b", "push_screen('home')", "HOME"),
        ("c", "push_screen('releases')", "RELEASES"),
        ("s", "push_screen('starred_repos')", "STARRED REPOS"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        self.engine = Engine()
        super().__init__(**kwargs)

    async def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self.install_screen(Home(), name="home")
        self.install_screen(Releases(), name="releases")
        self.install_screen(StarredRepos(), name="starred_repos")
        self.push_screen("home")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "checkReleases":
            self.notify("Loading new releases in background...")
            self.load_starred_releases_screen()
        elif button_id == "checkStarred":
            self.notify("Check starred button pressed!")
            self.load_starred_repos_screen()

    @work(exclusive=True)
    async def load_starred_repos_screen(self) -> None:
        self.push_screen("starred_repos")

    @work(exclusive=True)
    async def load_starred_releases_screen(self) -> None:
        self.push_screen("releases")


if __name__ == "__main__":
    app = GitHubFeed()
    app.run()
