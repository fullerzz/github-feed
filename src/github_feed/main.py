import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from rich.logging import RichHandler

from github_feed.engine import Engine, get_db_client
from github_feed.lib.models import Release
from github_feed.sql.models import Release as SqlRelease
from github_feed.sql.models import Repository

logging.basicConfig(
    handlers=[
        RotatingFileHandler("app.log", maxBytes=100_000, backupCount=10),
        RichHandler(rich_tracebacks=True, tracebacks_show_locals=False),
    ],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    db_client = get_db_client()  # trigger db creation
    yield
    del db_client


app = FastAPI(title="github-feed", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Welcome to the GitHub Feed API!"}


@app.get("/starred")
async def get_starred_repos(
    engine: Annotated[Engine, Depends(Engine)], refresh: bool = True
) -> list[Repository]:
    """
    Retrieve starred repositories from the database with the option to refresh the data.
    """
    repos = list(engine.retrieve_starred_repos(refresh=refresh))
    return repos


@app.get("/releases")
async def get_releases(
    engine: Annotated[Engine, Depends(Engine)], refresh: bool = False
) -> list[Release] | list[SqlRelease]:
    """
    Retrieve releases from the database with the option to refresh the data.
    """
    if refresh:
        logger.info("Refreshing releases")
        return await engine.retrieve_fresh_releases_async()
    else:
        return engine.retrieve_releases()
