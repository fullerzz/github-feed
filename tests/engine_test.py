import pytest

from github_feed.engine import DEFAULT_DB_FILENAME, Engine


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
