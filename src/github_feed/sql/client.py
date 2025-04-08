from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from github_feed.sql.models import Release, Repository, RunData, User


class DbClient:
    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, echo=True)
        SQLModel.metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))

    def add_user(self, user: User) -> None:
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

    def add_release(self, release: Release) -> None:
        with Session(self.engine) as session:
            session.add(release)
            session.commit()

    def add_repository(self, repository: Repository) -> None:
        with Session(self.engine) as session:
            session.add(repository)
            session.commit()

    def update_repository(self, repository: Repository) -> None:
        with Session(self.engine) as session:
            session.add(repository)
            session.commit()
            session.refresh(repository)

    def get_releases(self, start_time: datetime) -> Sequence[Release]:
        with Session(self.engine) as session:
            statement = select(Release).where(Release.created_at > start_time)
            results = session.exec(statement)
            return results.all()

    def get_repository(self, repo_id: int) -> Repository:
        with Session(self.engine) as session:
            statement = select(Repository).where(Repository.id == repo_id)
            results = session.exec(statement)
            return results.one()

    def get_starred_repos(self) -> Sequence[Repository]:
        with Session(self.engine) as session:
            statement = select(Repository)
            results = session.exec(statement)
            return results.all()

    def get_updated_repos(self, start_date: datetime) -> Sequence[Repository]:
        with Session(self.engine) as session:
            statement = (
                select(Repository).where(Repository.pushed_at != None).where(Repository.pushed_at > start_date)  # type: ignore  # noqa: E711
            )
            results = session.exec(statement)
            return results.all()

    def store_run(self, timestamp: datetime) -> None:
        with Session(self.engine) as session:
            session.add(RunData(executed_at=timestamp))
            session.commit()

    def get_last_run(self) -> RunData | None:
        # FIXME: This should order by executed_at and return the most recent RunData
        with Session(self.engine) as session:
            statement = select(RunData).order_by(RunData.executed_at.isoformat())
            results = session.exec(statement)
            data = results.first()
            return data
