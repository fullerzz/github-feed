from typing import Any

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView


class ReleasesList(Widget):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield ListView(ListItem(Label("1")), ListItem(Label("2")))
