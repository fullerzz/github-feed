import pathlib

import urllib3

from github_feed.models import LinkHeader, Repository


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
