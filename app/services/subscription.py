from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


class SubscriptionService:
    def __init__(self, url: str, stats_url: str, best_url: str, creator_url: str):
        self.url = url
        self.stats_url = stats_url
        self.best_url = best_url
        self.creator_url = creator_url

    async def stats(self) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                response = await client.get(self.stats_url)
                response.raise_for_status()
                return response.json()
        except Exception:
            return None


class AccessStore:
    """Small runtime access registry. Set ACCESS_FILE to a persistent path if desired."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv("ACCESS_FILE", ".data/best_access.json"))
        self.allowed: set[str] = set()
        self.pending: set[str] = set()
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.allowed = {str(x) for x in data.get("allowed", [])}
            self.pending = {str(x) for x in data.get("pending", [])}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.allowed = set()
            self.pending = set()

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"allowed": sorted(self.allowed), "pending": sorted(self.pending)}, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass

    def request(self, user_id: int) -> bool:
        uid = str(user_id)
        if uid in self.allowed:
            return False
        changed = uid not in self.pending
        self.pending.add(uid)
        self._save()
        return changed

    def approve(self, user_id: int) -> None:
        uid = str(user_id)
        self.pending.discard(uid)
        self.allowed.add(uid)
        self._save()

    def deny(self, user_id: int) -> None:
        self.pending.discard(str(user_id))
        self._save()

    def has_access(self, user_id: int) -> bool:
        return str(user_id) in self.allowed

    def pending_users(self) -> list[str]:
        return sorted(self.pending)
