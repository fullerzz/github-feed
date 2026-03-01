import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from textual.pilot import Pilot
from textual.widgets import DataTable, Label, ListItem, ListView, Markdown, Static

from github_feed.tui.app import (
    GitHubFeedApp,
    HomeScreen,
    ReleaseMode,
    ReleaseNotesScreen,
    ReleasesScreen,
    StarredReposScreen,
)

pytestmark = pytest.mark.enable_socket


@dataclass
class _RepositoryStub:
    full_name: str
    language: str | None
    stargazers_count: int
    pushed_at: datetime | None
    description: str | None


@dataclass
class _ReleaseStub:
    id: int | None
    html_url: str
    tag_name: str
    created_at: datetime
    body: str


class _EngineStub:
    def __init__(
        self,
        releases: Sequence[_ReleaseStub] = (),
        *,
        repos: Sequence[_RepositoryStub] = (),
        fail_starred: bool = False,
        fail_releases: bool = False,
    ) -> None:
        self._releases = list(releases)
        self._repos = list(repos)
        self._fail_starred = fail_starred
        self._fail_releases = fail_releases
        self.retrieve_releases_calls = 0
        self.retrieve_fresh_releases_calls = 0
        self.retrieve_starred_calls = 0

    async def retrieve_starred_repos(self, refresh: bool = False) -> Sequence[_RepositoryStub]:
        del refresh
        self.retrieve_starred_calls += 1
        if self._fail_starred:
            raise RuntimeError("Starred repos fetch failed")
        return self._repos

    def retrieve_releases_for_mode(
        self, window_days: int, all_history: bool = False
    ) -> Sequence[_ReleaseStub]:
        del window_days, all_history
        if self._fail_releases:
            raise RuntimeError("Releases fetch failed")
        self.retrieve_releases_calls += 1
        return self._releases

    async def retrieve_fresh_releases_for_mode(
        self, window_days: int, all_history: bool = False
    ) -> Sequence[_ReleaseStub]:
        del window_days, all_history
        if self._fail_releases:
            raise RuntimeError("Releases fetch failed")
        self.retrieve_fresh_releases_calls += 1
        return self._releases


async def _wait_for(predicate: Callable[[], bool], pilot: Pilot[None], max_wait: float = 2.0) -> None:
    deadline = time.monotonic() + max_wait
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail("Timed out waiting for UI state")
        await pilot.pause()


def _new_release() -> _ReleaseStub:
    return _ReleaseStub(
        id=1,
        html_url="https://github.com/example/repo/releases/tag/v1.2.3",
        tag_name="v1.2.3",
        created_at=datetime.now(UTC),
        body="## Highlights\n\n- Added a new feature",
    )


def _new_releases() -> list[_ReleaseStub]:
    return [
        _ReleaseStub(
            id=1,
            html_url="https://github.com/example/repo/releases/tag/v1.2.3",
            tag_name="v1.2.3",
            created_at=datetime.now(UTC),
            body="First release",
        ),
        _ReleaseStub(
            id=2,
            html_url="https://github.com/example/repo/releases/tag/v1.2.4",
            tag_name="v1.2.4",
            created_at=datetime.now(UTC),
            body="Second release",
        ),
    ]


def _new_repos() -> list[_RepositoryStub]:
    return [
        _RepositoryStub(
            full_name="example/beta",
            language="Python",
            stargazers_count=300,
            pushed_at=datetime.now(UTC),
            description="Beta project",
        ),
        _RepositoryStub(
            full_name="example/alpha",
            language="TypeScript",
            stargazers_count=150,
            pushed_at=datetime.now(UTC),
            description="Alpha project",
        ),
        _RepositoryStub(
            full_name="example/gamma",
            language=None,
            stargazers_count=50,
            pushed_at=None,
            description=None,
        ),
    ]


def _release_list_populated(app: GitHubFeedApp) -> bool:
    if not isinstance(app.screen, ReleasesScreen):
        return False
    release_list = app.screen.query_one("#release-list", ListView)
    return len(release_list.children) > 0


@pytest.mark.asyncio
async def test_releases_right_arrow_opens_full_release_notes_screen() -> None:
    app = GitHubFeedApp(engine=_EngineStub([_new_release()]))

    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)

        await pilot.press("right")
        await _wait_for(lambda: isinstance(app.screen, ReleaseNotesScreen), pilot)

        notes_screen = app.screen
        assert isinstance(notes_screen, ReleaseNotesScreen)
        notes = notes_screen.query_one("#release-notes-page", Markdown)
        assert notes is not None


@pytest.mark.asyncio
async def test_release_notes_left_arrow_returns_to_releases_screen() -> None:
    engine = _EngineStub(_new_releases())
    app = GitHubFeedApp(engine=engine)

    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)
        initial_retrieve_calls = engine.retrieve_releases_calls

        releases_screen = app.screen
        assert isinstance(releases_screen, ReleasesScreen)
        release_list = releases_screen.query_one("#release-list", ListView)

        await pilot.press("down")
        await _wait_for(lambda: release_list.index == 1, pilot)

        await pilot.press("right")
        await _wait_for(lambda: isinstance(app.screen, ReleaseNotesScreen), pilot)

        await pilot.press("left")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await pilot.pause()

        releases_screen = app.screen
        assert isinstance(releases_screen, ReleasesScreen)
        release_list = releases_screen.query_one("#release-list", ListView)
        await _wait_for(lambda: release_list.index == 1, pilot)
        assert release_list.index == 1
        assert app.focused is release_list

        items = release_list.query("ListItem").results(ListItem)
        assert [item.highlighted for item in items] == [False, True]
        assert engine.retrieve_releases_calls == initial_retrieve_calls


@pytest.mark.asyncio
async def test_manual_refresh_invalidates_other_mode_release_cache() -> None:
    engine = _EngineStub(_new_releases())
    app = GitHubFeedApp(engine=engine)

    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)
        initial_retrieve_calls = engine.retrieve_releases_calls

        await pilot.press("m")
        await _wait_for(lambda: engine.retrieve_releases_calls == initial_retrieve_calls + 1, pilot)

        await pilot.press("m")
        await pilot.pause()
        assert engine.retrieve_releases_calls == initial_retrieve_calls + 1

        releases_screen = app.screen
        assert isinstance(releases_screen, ReleasesScreen)
        releases_screen.load_releases(refresh=True)
        await _wait_for(lambda: engine.retrieve_fresh_releases_calls == 1, pilot)

        await pilot.press("m")
        await _wait_for(lambda: engine.retrieve_releases_calls == initial_retrieve_calls + 2, pilot)


# --- HomeScreen Tests ---


@pytest.mark.asyncio
async def test_home_screen_renders_metadata() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        metadata = app.screen.query_one("#home-metadata", Static)
        text = str(metadata.content)
        assert "Mode:" in text
        assert "Release window:" in text
        assert "GITHUB_TOKEN:" in text
        assert "DB_FILENAME:" in text


@pytest.mark.asyncio
async def test_home_screen_starred_button_navigates() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        await pilot.click("#open-starred")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)
        assert isinstance(app.screen, StarredReposScreen)


@pytest.mark.asyncio
async def test_home_screen_releases_button_navigates() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        await pilot.click("#open-releases")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        assert isinstance(app.screen, ReleasesScreen)


@pytest.mark.asyncio
async def test_home_screen_shows_startup_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    app = GitHubFeedApp()
    async with app.run_test() as pilot:
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        metadata = app.screen.query_one("#home-metadata", Static)
        text = str(metadata.content)
        assert "Missing GITHUB_TOKEN" in text


# --- StarredReposScreen Tests ---


@pytest.mark.asyncio
async def test_starred_repos_load_sorted_by_stars_desc() -> None:
    repos = _new_repos()
    app = GitHubFeedApp(engine=_EngineStub(repos=repos))
    async with app.run_test() as pilot:
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)

        table = app.screen.query_one("#starred-table", DataTable)
        await _wait_for(lambda: table.row_count == 3, pilot)

        row0 = table.get_row_at(0)
        row2 = table.get_row_at(2)
        assert row0[0] == "example/beta"  # 300 stars, highest
        assert row2[1] == "-"  # None language → "-"


@pytest.mark.asyncio
async def test_starred_repos_refresh_triggers_reload() -> None:
    repos = _new_repos()
    engine = _EngineStub(repos=repos)
    app = GitHubFeedApp(engine=engine)
    async with app.run_test() as pilot:
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)

        status = app.screen.query_one("#starred-status", Label)
        await _wait_for(lambda: "Loaded" in str(status.content), pilot)
        initial_calls = engine.retrieve_starred_calls

        await pilot.click("#refresh-starred")
        await _wait_for(lambda: engine.retrieve_starred_calls > initial_calls, pilot)
        assert "Loaded" in str(status.content)


@pytest.mark.asyncio
async def test_starred_repos_empty_state() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)

        status = app.screen.query_one("#starred-status", Label)
        await _wait_for(lambda: "Loaded 0 repositories" in str(status.content), pilot)

        table = app.screen.query_one("#starred-table", DataTable)
        assert table.row_count == 0


@pytest.mark.asyncio
async def test_starred_repos_error_shows_failure() -> None:
    app = GitHubFeedApp(engine=_EngineStub(fail_starred=True))
    async with app.run_test() as pilot:
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)

        status = app.screen.query_one("#starred-status", Label)
        await _wait_for(lambda: "Failed to load starred repositories" in str(status.content), pilot)
        assert "Failed to load starred repositories" in str(status.content)


# --- ReleasesScreen Tests ---


@pytest.mark.asyncio
async def test_releases_initial_load_populates_list() -> None:
    engine = _EngineStub(_new_releases())
    app = GitHubFeedApp(engine=engine)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)

        release_list = app.screen.query_one("#release-list", ListView)
        assert len(release_list.children) == 2

        status = app.screen.query_one("#release-status", Label)
        assert "Loaded 2 releases" in str(status.content)


@pytest.mark.asyncio
async def test_releases_selecting_shows_notes_in_viewer() -> None:
    releases = _new_releases()
    engine = _EngineStub(releases)
    app = GitHubFeedApp(engine=engine)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)

        releases_screen = app.screen
        assert isinstance(releases_screen, ReleasesScreen)

        # First release auto-selected on load
        assert releases_screen._selected_release_index == 0

        # Navigate to second release
        release_list = releases_screen.query_one("#release-list", ListView)
        await pilot.press("down")
        await _wait_for(lambda: release_list.index == 1, pilot)
        assert releases_screen._selected_release_index == 1


@pytest.mark.asyncio
async def test_releases_empty_state() -> None:
    engine = _EngineStub()
    app = GitHubFeedApp(engine=engine)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)

        status = app.screen.query_one("#release-status", Label)
        await _wait_for(lambda: "Loaded 0 releases" in str(status.content), pilot)

        release_list = app.screen.query_one("#release-list", ListView)
        assert len(release_list.children) == 0


@pytest.mark.asyncio
async def test_releases_error_shows_failure() -> None:
    engine = _EngineStub(fail_releases=True)
    app = GitHubFeedApp(engine=engine)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)

        status = app.screen.query_one("#release-status", Label)
        await _wait_for(lambda: "Failed to load releases" in str(status.content), pilot)
        assert "Failed to load releases" in str(status.content)


# --- Global Navigation Tests ---


@pytest.mark.asyncio
async def test_key_h_returns_home_from_starred() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)
        await pilot.press("h")
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_key_h_returns_home_from_releases() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await pilot.press("h")
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_key_s_navigates_to_starred() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)
        assert isinstance(app.screen, StarredReposScreen)


@pytest.mark.asyncio
async def test_key_m_toggles_release_mode() -> None:
    app = GitHubFeedApp(engine=_EngineStub())
    async with app.run_test() as pilot:
        await _wait_for(lambda: isinstance(app.screen, HomeScreen), pilot)
        assert app.release_mode == ReleaseMode.RECENT
        await pilot.press("m")
        assert app.release_mode == ReleaseMode.ALL_HISTORY
        await pilot.press("m")
        assert app.release_mode == ReleaseMode.RECENT


# --- ReleaseNotesScreen Test ---


@pytest.mark.asyncio
async def test_release_notes_back_button_returns() -> None:
    engine = _EngineStub([_new_release()])
    app = GitHubFeedApp(engine=engine)
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)

        await pilot.press("right")
        await _wait_for(lambda: isinstance(app.screen, ReleaseNotesScreen), pilot)

        await pilot.click("#release-notes-back")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        assert isinstance(app.screen, ReleasesScreen)


# --- No-Engine Error Tests ---


@pytest.mark.asyncio
async def test_no_engine_starred_shows_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    app = GitHubFeedApp()
    async with app.run_test() as pilot:
        await pilot.press("s")
        await _wait_for(lambda: isinstance(app.screen, StarredReposScreen), pilot)

        status = app.screen.query_one("#starred-status", Label)
        await _wait_for(lambda: "No engine available" in str(status.content), pilot)
        assert "No engine available" in str(status.content)


@pytest.mark.asyncio
async def test_no_engine_releases_shows_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    app = GitHubFeedApp()
    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)

        status = app.screen.query_one("#release-status", Label)
        await _wait_for(lambda: "No engine available" in str(status.content), pilot)
        assert "No engine available" in str(status.content)
