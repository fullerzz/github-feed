import logging
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from os import environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from github_feed.engine import get_db_client
from github_feed.github_client import GitHubClient
from github_feed.models import Repository

logging.basicConfig(
    handlers=[
        RotatingFileHandler("app.log", maxBytes=100_000, backupCount=10),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    db_client = get_db_client()
    yield
    del db_client


gh_client = GitHubClient(environ["GITHUB_TOKEN"])
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
async def get_starred_repos() -> list[Repository]:
    """
    Retrieve starred repositories from the database.
    """
    repos = gh_client.get_starred_repositories()
    return repos
