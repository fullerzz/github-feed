from typing import Any

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Collapsible, Label, ListItem, ListView, Markdown

JESSICA = """
# Lady Jessica

Bene Gesserit and concubine of Leto, and mother of Paul and Alia.
"""

names = ["Paul", "Leto", "Alia", "Ghanima", "Irulan", "Chani", "Stilgar", "Duncan", "Thufir", "Gurney"]


class ReleasesList(Widget):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        items: list[ListItem] = [
            ListItem(Collapsible(Label(f"Nested content for {name}"), title=name)) for name in names
        ]

        yield ListView(
            ListItem(Label("1")),
            ListItem(Label("2")),
            ListItem(Collapsible(Markdown(JESSICA), collapsed=False, title="Jessica")),
            *items,
        )
