from sqlmodel import Session, SQLModel, create_engine

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
