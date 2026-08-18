from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_user_id: str
    subscription_url: str
    best_url: str
    creator_url: str
    stats_url: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is not configured")
        admin = os.getenv("ADMIN_USER_ID", "").strip()
        base = os.getenv("NEYRA_BASE_URL", "https://londonslayer1337.github.io/neyra-vpn").rstrip("/")
        return cls(
            bot_token=token,
            admin_user_id=admin,
            subscription_url=os.getenv("SUBSCRIPTION_URL", f"{base}/sub/public.txt"),
            best_url=os.getenv("BEST_SUBSCRIPTION_URL", f"{base}/sub/best.txt"),
            creator_url=os.getenv("CREATOR_SUBSCRIPTION_URL", f"{base}/sub/creator.txt"),
            stats_url=os.getenv("SUB_STATS_URL", f"{base}/sub/stats.json"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
