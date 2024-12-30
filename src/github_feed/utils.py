import pathlib

import urllib3

from github_feed.models import LinkHeader, Repository
from github_feed.sql.models import Repository as SqlRepository



def save_starred_repos(repos: list[Repository], filename: str) -> None:
    with pathlib.Path(filename).open("w") as file:
        file.write("[\n")
        for i, repo in enumerate(repos):
            file.write(f"{repo.model_dump_json(indent=2)}")
            if i < len(repos) - 1:
                file.write(",\n")
            else:
                file.write("\n")
        file.write("]\n")


def _clean_link(link: str) -> str:
    link = link.strip()
    link = link.lstrip("<")
    link = link.rstrip(">")
    return link


def parse_link_header(headers: urllib3.HTTPHeaderDict) -> LinkHeader:
    link_header = headers.get("link")
    if link_header:
        parts = link_header.split(",")
        links = {}
        for part in parts:
            if 'rel="prev"' in part:
                prev = part.split(";")[0].strip("<>")
                prev = _clean_link(prev)
                links["prev"] = prev
            elif 'rel="next"' in part:
                next = part.split(";")[0].strip("<>")
                next = _clean_link(next)
                links["next"] = next
            elif 'rel="first"' in part:
                first = part.split(";")[0].strip("<>")
                first = _clean_link(first)
                links["first"] = first
            elif 'rel="last"' in part:
                last = part.split(";")[0].strip(" <>")
                last = _clean_link(last)
                links["last"] = last
        return LinkHeader(**links)
    return LinkHeader()


def extract_repo_name_from_html_url(html_url: str) -> str:
    # FIXME: See https://github.com/fullerzz/github-feed/issues/9
    # Example: https://github.com/leptos-rs/leptos/releases/tag/v0.7.2
    url_parts = html_url.split("/")
    return url_parts[-4]

def update_existing_repo(existing: SqlRepository, fresh: Repository) -> SqlRepository:
    existing.description = fresh.description
    existing.stargazers_count = fresh.stargazers_count
    existing.forks_count = fresh.forks_count
    existing.watchers_count = fresh.watchers_count
    existing.watchers = fresh.watchers
    existing.pushed_at = fresh.pushed_at
    existing.updated_at = fresh.updated_at
    existing.homepage = fresh.homepage
    existing.size = fresh.size
    existing.open_issues = fresh.open_issues
    existing.open_issues_count = fresh.open_issues_count
    return existing