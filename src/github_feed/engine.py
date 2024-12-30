from typing import Sequence
from functools import cache
from os import getenv

from pydantic import BaseModel, SecretStr
from sqlalchemy.exc import IntegrityError, NoResultFound

from github_feed.github_client import GitHubClient
from github_feed.models import Repository
from github_feed.sql.client import DbClient
from github_feed.sql.models import Repository as SqlRepository


@cache
def get_db_client(filename: str) -> DbClient:
    return DbClient(f"sqlite:///{filename}")


class Config(BaseModel):
    db_filename: str = "stargazing.db"
    github_token: SecretStr


class Engine:
    def __init__(self) -> None:
        self.config = self.load_config()
        self.db = get_db_client(filename=self.config.db_filename)
        self.gh_client = GitHubClient(self.config.github_token.get_secret_value())

    def load_config(self) -> Config:
        db_filename = getenv("DB_FILENAME")
        github_token = getenv("GITHUB_TOKEN")
        config_inputs = {"github_token": github_token}
        if db_filename is not None:
            config_inputs["db_filename"] = db_filename
        return Config(**config_inputs)  # type: ignore[arg-type]

    def retrieve_starred_repos(self, refresh: bool = False) -> Sequence[SqlRepository]:
        """
        Returns list of starred repositories from the db.
        """
        if refresh:
            self.refresh_starred_repos()
        starred_repos = self.db.get_starred_repos()
        return starred_repos

    def refresh_starred_repos(self) -> None:
        """
        Retrieve starred repos from GitHub and populate the database.
        """
        starred_repos = self.gh_client.get_starred_repositories()
        for repo in starred_repos:
            self._refresh_starred_repo_in_table(repo)

    def _refresh_starred_repo_in_table(self, repo: Repository) -> None:
        """
        Inserts starred repo into table if not already present. Otherwise, the existing starred repo
        is updated with fresh data from the GitHub API.
        """
        raw_repo = repo.model_dump()
        try:
            self.db.add_repository(SqlRepository(**raw_repo))
        except IntegrityError:
            # Repo already exists in the db, so try to retrieve the existing row
            try:
                existing_row = self.db.get_repository(repo.id)
            except NoResultFound:
                # TODO: Log this error and decide how to handle it
                return None
            raw_existing_repo = existing_row.model_dump()
            updated_repo_data = raw_existing_repo | raw_repo  # Update existing data with fresh data from raw_repo
            self.db.update_repository(SqlRepository(**updated_repo_data))
            return None
