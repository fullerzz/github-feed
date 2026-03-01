from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from types import MethodType
from typing import Any

import pytest

from github_feed.engine import DEFAULT_DB_FILENAME, DEFAULT_RELEASE_WINDOW_DAYS, Engine


class _ReleaseRow:
    def __init__(self, created_at: datetime) -> None:
        self.created_at = created_at


class _RepoRow:
    def __init__(self, full_name: str, releases_url: str) -> None:
        self.full_name = full_name
        self.releases_url = releases_url


class _FreshModeDb:
    def __init__(self, starred_repos: list[_RepoRow], updated_repos: list[_RepoRow]) -> None:
        self._starred_repos = starred_repos
        self._updated_repos = updated_repos
        self.updated_start_time: datetime | None = None

    def get_starred_repos(self) -> list[_RepoRow]:
        return self._starred_repos

    def get_updated_repos(self, start_date: datetime) -> list[_RepoRow]:
        self.updated_start_time = start_date
        return self._updated_repos


def _new_engine() -> Engine:
    return Engine.__new__(Engine)


def _run_immediate_coroutine(coroutine: Coroutine[Any, Any, Any]) -> Any:
    try:
        coroutine.send(None)
    except StopIteration as stop:
        return stop.value
    raise AssertionError("Coroutine yielded unexpectedly")


@pytest.mark.parametrize(
    ("db_filename_env_var", "expected_db_filename"), [(None, DEFAULT_DB_FILENAME), ("test.db", "test.db")]
)
def test_load_config(
    monkeypatch: pytest.MonkeyPatch, db_filename_env_var: str | None, expected_db_filename: str
) -> None:
    mock_token = "fake_token"  # noqa: S105
    monkeypatch.setenv("GITHUB_TOKEN", mock_token)
    if db_filename_env_var is not None:
        monkeypatch.setenv("DB_FILENAME", db_filename_env_var)
    engine = Engine()
    assert engine.config.db_filename == expected_db_filename
    assert engine.config.github_token.get_secret_value() == mock_token


def test_retrieve_releases_for_mode_all_history_sorts_descending() -> None:
    now = datetime.now(UTC)
    older = _ReleaseRow(created_at=now - timedelta(days=2))
    newer = _ReleaseRow(created_at=now)

    class _DbStub:
        def get_all_releases(self) -> list[_ReleaseRow]:
            return [older, newer]

    engine = _new_engine()
    engine.db = _DbStub()  # type: ignore[attr-defined]

    releases = engine.retrieve_releases_for_mode(all_history=True)
    assert releases == [newer, older]


def test_retrieve_releases_for_mode_recent_passes_configured_window() -> None:
    engine = _new_engine()
    observed: dict[str, datetime] = {}

    def _fake_retrieve_releases(start_time: datetime | None) -> list[_ReleaseRow]:
        assert start_time is not None
        observed["start_time"] = start_time
        return []

    engine.retrieve_releases = _fake_retrieve_releases  # type: ignore[method-assign]

    now_before = datetime.now(UTC)
    releases = engine.retrieve_releases_for_mode(window_days=7, all_history=False)
    now_after = datetime.now(UTC)

    expected_min = now_before - timedelta(days=7, seconds=1)
    expected_max = now_after - timedelta(days=7) + timedelta(seconds=1)
    assert releases == []
    assert expected_min <= observed["start_time"] <= expected_max


def test_retrieve_fresh_releases_for_mode_all_history_uses_starred_repos() -> None:
    repos = [
        _RepoRow(full_name="example/repo", releases_url="https://api.github.com/repos/example/repo/releases")
    ]
    db = _FreshModeDb(starred_repos=repos, updated_repos=[])

    engine = _new_engine()
    engine.db = db  # type: ignore[attr-defined]
    observed: dict[str, object] = {}

    async def _fake_helper(
        _self: Engine, repo_rows: list[_RepoRow], start_time: datetime | None
    ) -> list[object]:
        observed["repos"] = repo_rows
        observed["start_time"] = start_time
        return []

    engine._retrieve_fresh_releases_for_repos = MethodType(  # type: ignore[method-assign]
        _fake_helper, engine
    )

    releases = _run_immediate_coroutine(engine.retrieve_fresh_releases_for_mode(all_history=True))
    assert releases == []
    assert observed["repos"] == repos
    assert observed["start_time"] is None


def test_retrieve_fresh_releases_for_mode_recent_uses_windowed_updated_repos() -> None:
    repos = [
        _RepoRow(full_name="example/repo", releases_url="https://api.github.com/repos/example/repo/releases")
    ]
    db = _FreshModeDb(starred_repos=[], updated_repos=repos)

    engine = _new_engine()
    engine.db = db  # type: ignore[attr-defined]
    observed: dict[str, object] = {}

    async def _fake_helper(
        _self: Engine, repo_rows: list[_RepoRow], start_time: datetime | None
    ) -> list[object]:
        observed["repos"] = repo_rows
        observed["start_time"] = start_time
        return []

    engine._retrieve_fresh_releases_for_repos = MethodType(  # type: ignore[method-assign]
        _fake_helper, engine
    )

    now_before = datetime.now(UTC)
    releases = _run_immediate_coroutine(
        engine.retrieve_fresh_releases_for_mode(
            window_days=DEFAULT_RELEASE_WINDOW_DAYS,
            all_history=False,
        )
    )
    now_after = datetime.now(UTC)

    assert releases == []
    assert observed["repos"] == repos
    assert isinstance(observed["start_time"], datetime)
    assert db.updated_start_time == observed["start_time"]

    expected_min = now_before - timedelta(days=DEFAULT_RELEASE_WINDOW_DAYS, seconds=1)
    expected_max = now_after - timedelta(days=DEFAULT_RELEASE_WINDOW_DAYS) + timedelta(seconds=1)
    assert expected_min <= observed["start_time"] <= expected_max
