from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    uri: str
    scheme: str
    source: str
    score: int = 0
    label: str = ""
