from os import environ

from rich.pretty import pprint
from rich.traceback import install

from github_feed import engine, utils
from github_feed.github_client import GitHubClient

install(show_locals=False)


def retrieve_activity() -> None:
    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    resp = client.get_user()
    pprint(resp)
    starred = client.get_starred_repositories()
    utils.save_starred_repos(starred, "starred_repos.json")


if __name__ == "__main__":
    retrieve_activity()
    engine.get_new_releases()
