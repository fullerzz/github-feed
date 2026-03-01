import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from textual.pilot import Pilot
from textual.widgets import ListItem, ListView, Markdown

from github_feed.tui.app import GitHubFeedApp, ReleaseNotesScreen, ReleasesScreen

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
    def __init__(self, releases: Sequence[_ReleaseStub]) -> None:
        self._releases = list(releases)

    async def retrieve_starred_repos(self, refresh: bool = False) -> Sequence[_RepositoryStub]:
        del refresh
        return []

    def retrieve_releases_for_mode(
        self, window_days: int, all_history: bool = False
    ) -> Sequence[_ReleaseStub]:
        del window_days, all_history
        return self._releases

    async def retrieve_fresh_releases_for_mode(
        self, window_days: int, all_history: bool = False
    ) -> Sequence[_ReleaseStub]:
        del window_days, all_history
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
    app = GitHubFeedApp(engine=_EngineStub(_new_releases()))

    async with app.run_test() as pilot:
        await pilot.press("r")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)
        await _wait_for(lambda: _release_list_populated(app), pilot)

        releases_screen = app.screen
        assert isinstance(releases_screen, ReleasesScreen)
        release_list = releases_screen.query_one("#release-list", ListView)

        await pilot.press("down")
        await _wait_for(lambda: release_list.index == 1, pilot)

        await pilot.press("right")
        await _wait_for(lambda: isinstance(app.screen, ReleaseNotesScreen), pilot)

        await pilot.press("left")
        await _wait_for(lambda: isinstance(app.screen, ReleasesScreen), pilot)

        releases_screen = app.screen
        assert isinstance(releases_screen, ReleasesScreen)
        release_list = releases_screen.query_one("#release-list", ListView)
        await _wait_for(lambda: release_list.index == 1, pilot)
        assert release_list.index == 1
        assert app.focused is release_list

        items = release_list.query("ListItem").results(ListItem)
        assert [item.highlighted for item in items] == [False, True]
