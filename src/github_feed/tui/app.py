from __future__ import annotations

import os
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import ClassVar, Protocol, cast
from urllib.parse import urlparse

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, ListItem, ListView, Markdown, Static

from github_feed.engine import DEFAULT_RELEASE_WINDOW_DAYS, Engine


class RepositoryLike(Protocol):
    full_name: str
    language: str | None
    stargazers_count: int
    pushed_at: datetime | None
    description: str | None


class ReleaseLike(Protocol):
    id: int | None
    html_url: str
    tag_name: str
    created_at: datetime
    body: str


class EngineLike(Protocol):
    async def retrieve_starred_repos(self, refresh: bool = False) -> Sequence[RepositoryLike]: ...

    def retrieve_releases_for_mode(
        self, window_days: int, all_history: bool = False
    ) -> Sequence[ReleaseLike]: ...

    async def retrieve_fresh_releases_for_mode(
        self, window_days: int, all_history: bool = False
    ) -> Sequence[ReleaseLike]: ...


class ReleaseMode(StrEnum):
    RECENT = "recent"
    ALL_HISTORY = "all-history"


def _feed_app(screen: Screen[None]) -> GitHubFeedApp:
    return cast(GitHubFeedApp, screen.app)


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _repo_name_from_release_url(url: str) -> str:
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    if len(path_parts) >= 2:
        return f"{path_parts[0]}/{path_parts[1]}"
    return "unknown/unknown"


class HomeScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="home-layout"):
            yield Static("GitHub Feed", id="home-title")
            yield Static("", id="home-metadata")
            with Horizontal(id="home-actions"):
                yield Button("Starred Repos", id="open-starred", variant="primary")
                yield Button("Releases", id="open-releases", variant="success")
                yield Button("Toggle Release Mode", id="toggle-mode")
        yield Footer()

    def on_mount(self) -> None:
        self.update_metadata()

    def on_screen_resume(self) -> None:
        self.update_metadata()

    def update_metadata(self) -> None:
        app = _feed_app(self)
        mode_text = app.release_mode_label
        lines = [
            f"Mode: {mode_text}",
            f"Release window: {app.release_window_days} days",
            f"Last release refresh: {_format_timestamp(app.last_release_refresh_at)}",
            f"GITHUB_TOKEN: {'present' if os.getenv('GITHUB_TOKEN') else 'missing'}",
            f"DB_FILENAME: {os.getenv('DB_FILENAME', 'data/stargazing.db')}",
        ]
        if app.startup_error is not None:
            lines.append(f"Status: {app.startup_error}")
        self.query_one("#home-metadata", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = _feed_app(self)
        button_id = event.button.id
        if button_id == "open-starred":
            app.action_show_starred()
        elif button_id == "open-releases":
            app.action_show_releases()
        elif button_id == "toggle-mode":
            app.action_toggle_mode()


class StarredReposScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="starred-layout"):
            with Horizontal(classes="toolbar"):
                yield Button("Back", id="back-home")
                yield Button("Refresh", id="refresh-starred", variant="primary")
            yield Label("", id="starred-status")
            yield DataTable(id="starred-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#starred-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Repository", "Language", "Stars", "Last Push", "Description")
        self.load_starred_repos(refresh=False)

    def on_screen_resume(self) -> None:
        self.load_starred_repos(refresh=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = _feed_app(self)
        button_id = event.button.id
        if button_id == "back-home":
            app.action_show_home()
        elif button_id == "refresh-starred":
            self.load_starred_repos(refresh=True)

    @work(exclusive=True)
    async def load_starred_repos(self, refresh: bool) -> None:
        app = _feed_app(self)
        table = self.query_one("#starred-table", DataTable)
        status = self.query_one("#starred-status", Label)
        if not app.has_engine:
            status.update("No engine available. Set GITHUB_TOKEN and restart.")
            return

        self.loading = True
        mode = "refreshing" if refresh else "loading"
        status.update(f"{mode.capitalize()} starred repositories...")
        try:
            repos = list(await app.engine.retrieve_starred_repos(refresh=refresh))
            repos.sort(key=lambda repo: repo.stargazers_count, reverse=True)

            table.clear(columns=False)
            for repo in repos:
                table.add_row(
                    repo.full_name,
                    repo.language or "-",
                    str(repo.stargazers_count),
                    _format_timestamp(repo.pushed_at),
                    (repo.description or "").strip() or "-",
                )
            status.update(f"Loaded {len(repos)} repositories.")
        except Exception as error:
            status.update(f"Failed to load starred repositories: {error}")
        finally:
            self.loading = False


class ReleasesScreen(Screen[None]):
    _releases: list[ReleaseLike]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="releases-layout"):
            with Horizontal(classes="toolbar"):
                yield Button("Back", id="release-back")
                yield Button("Toggle Mode", id="release-toggle-mode")
                yield Button("Refresh", id="refresh-releases", variant="primary")
            yield Label("", id="release-status")
            with Horizontal(id="release-content"):
                yield ListView(id="release-list")
                yield Markdown("Select a release to view notes.", id="release-notes")
        yield Footer()

    def on_mount(self) -> None:
        self._releases = []
        self.load_releases(refresh=False)

    def on_screen_resume(self) -> None:
        self.load_releases(refresh=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = _feed_app(self)
        button_id = event.button.id
        if button_id == "release-back":
            app.action_show_home()
        elif button_id == "release-toggle-mode":
            app.action_toggle_mode()
        elif button_id == "refresh-releases":
            self.load_releases(refresh=True)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "release-list":
            return
        self._show_release_notes(event.list_view.index)

    @work(exclusive=True)
    async def load_releases(self, refresh: bool) -> None:
        app = _feed_app(self)
        status = self.query_one("#release-status", Label)
        if not app.has_engine:
            status.update("No engine available. Set GITHUB_TOKEN and restart.")
            return

        self.loading = True
        mode_text = app.release_mode_label
        status.update(f"Loading releases ({mode_text})...")
        try:
            if refresh:
                releases = await app.engine.retrieve_fresh_releases_for_mode(
                    window_days=app.release_window_days,
                    all_history=app.release_mode == ReleaseMode.ALL_HISTORY,
                )
                app.last_release_refresh_at = datetime.now(UTC)
            else:
                releases = app.engine.retrieve_releases_for_mode(
                    window_days=app.release_window_days,
                    all_history=app.release_mode == ReleaseMode.ALL_HISTORY,
                )

            self._releases = list(releases)
            self._render_release_list()
            status.update(f"Loaded {len(self._releases)} releases ({mode_text}).")
        except Exception as error:
            status.update(f"Failed to load releases: {error}")
        finally:
            self.loading = False

    def _render_release_list(self) -> None:
        list_view = self.query_one("#release-list", ListView)
        list_view.clear()

        for release in self._releases:
            repository = _repo_name_from_release_url(release.html_url)
            title = f"{repository} | {release.tag_name} | {_format_timestamp(release.created_at)}"
            list_view.append(ListItem(Label(title, classes="release-item")))

        if self._releases:
            list_view.index = 0
            self._show_release_notes(0)
        else:
            self.query_one("#release-notes", Markdown).update("No releases found for the current mode.")

    def _show_release_notes(self, index: int | None) -> None:
        markdown = self.query_one("#release-notes", Markdown)
        if index is None or index < 0 or index >= len(self._releases):
            markdown.update("Select a release to view notes.")
            return

        release = self._releases[index]
        repository = _repo_name_from_release_url(release.html_url)
        notes = release.body.strip() or "_No release notes provided._"
        markdown.update(
            "\n".join(
                [
                    f"# {repository} - {release.tag_name}",
                    f"Created: {_format_timestamp(release.created_at)}",
                    "",
                    notes,
                ]
            )
        )


class GitHubFeedApp(App[None]):
    CSS_PATH = "app.tcss"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("h", "show_home", "Home"),
        Binding("s", "show_starred", "Starred"),
        Binding("r", "show_releases", "Releases"),
        Binding("m", "toggle_mode", "Toggle Mode"),
        Binding("q", "quit", "Quit"),
    ]

    release_mode: reactive[ReleaseMode] = reactive(ReleaseMode.RECENT)
    release_window_days: reactive[int] = reactive(DEFAULT_RELEASE_WINDOW_DAYS)
    last_release_refresh_at: reactive[datetime | None] = reactive(None)
    startup_error: reactive[str | None] = reactive(None)

    def __init__(
        self,
        engine: EngineLike | None = None,
        release_window_days: int | None = None,
    ) -> None:
        super().__init__()
        self._engine = engine
        env_window = os.getenv("RELEASE_WINDOW_DAYS")
        window_days = release_window_days
        if window_days is None and env_window is not None:
            try:
                window_days = int(env_window)
            except ValueError:
                window_days = DEFAULT_RELEASE_WINDOW_DAYS
        if window_days is None:
            window_days = DEFAULT_RELEASE_WINDOW_DAYS
        self.release_window_days = max(window_days, 1)

    @property
    def engine(self) -> EngineLike:
        if self._engine is None:
            raise RuntimeError("Engine not initialized")
        return cast(EngineLike, self._engine)

    @property
    def has_engine(self) -> bool:
        return self._engine is not None

    @property
    def release_mode_label(self) -> str:
        if self.release_mode == ReleaseMode.ALL_HISTORY:
            return "All History"
        return f"Recent ({self.release_window_days}d)"

    def on_mount(self) -> None:
        if self._engine is None:
            try:
                self._engine = Engine()
            except KeyError:
                self.startup_error = "Missing GITHUB_TOKEN. Set it before running the TUI."

        self.install_screen(HomeScreen(), "home")
        self.install_screen(StarredReposScreen(), "starred")
        self.install_screen(ReleasesScreen(), "releases")
        self.push_screen("home")

    def action_show_home(self) -> None:
        self.switch_screen("home")

    def action_show_starred(self) -> None:
        self.switch_screen("starred")

    def action_show_releases(self) -> None:
        self.switch_screen("releases")

    def action_toggle_mode(self) -> None:
        if self.release_mode == ReleaseMode.RECENT:
            self.release_mode = ReleaseMode.ALL_HISTORY
        else:
            self.release_mode = ReleaseMode.RECENT

        if isinstance(self.screen, HomeScreen):
            self.screen.update_metadata()
        elif isinstance(self.screen, ReleasesScreen):
            self.screen.load_releases(refresh=False)
