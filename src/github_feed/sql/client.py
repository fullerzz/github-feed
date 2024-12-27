from collections.abc import Sequence
from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine, select

from github_feed.sql.models import Repository, User


class DbClient:
    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, echo=True)
        SQLModel.metadata.create_all(self.engine)

    def add_user(self, user: User) -> None:
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

    def add_repository(self, repository: Repository) -> None:
        with Session(self.engine) as session:
            session.add(repository)
            session.commit()

    def get_updated_repos(self, start_date: datetime) -> Sequence[Repository]:
        with Session(self.engine) as session:
            statement = (
                select(Repository).where(Repository.pushed_at is not None).where(Repository.pushed_at > start_date)  # type: ignore
            )
            results = session.exec(statement)
            return results.all()
