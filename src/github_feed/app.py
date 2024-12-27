from os import environ

from rich.pretty import pprint
from rich.traceback import install

from github_feed.github_client import GitHubClient

install(show_locals=False)


def retrieve_activity() -> None:
    token = environ["GITHUB_TOKEN"]
    client = GitHubClient(token)
    resp = client.get_user()
    pprint(resp)
    starred = client.get_starred_repositories()
    pprint(starred)


if __name__ == "__main__":
    retrieve_activity()
