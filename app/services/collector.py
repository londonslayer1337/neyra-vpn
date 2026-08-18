from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import re
import uuid
from urllib.parse import unquote, urlsplit

import httpx

from app.core.models import Node

log = logging.getLogger(__name__)

SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/morteza-f/VPN-Configs/main/Configs/Vless.txt",
    "https://raw.githubusercontent.com/Ezzatkhah/VPN-Configs/main/Configs/Vless.txt",
]
SCHEMES = {"vless", "vmess", "trojan", "ss", "socks", "socks5", "hysteria2", "hy2", "tuic"}
URI_RE = re.compile(r"(?i)(?:^|\s|[`'\"(])((?:vless|vmess|trojan|ss|socks5?|hysteria2?|hy2|tuic)://[^\s`'\"<>]+)")


def maybe_decode_base64(text: str) -> str:
    compact = "".join(text.split())
    if len(compact) < 16 or not re.fullmatch(r"[A-Za-z0-9+/=_-]+", compact):
        return text
    padded = compact.replace("-", "+").replace("_", "/")
    padded += "=" * (-len(padded) % 4)
    try:
        decoded = base64.b64decode(padded, validate=False).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return text
    return decoded if "://" in decoded else text


def extract_uris(text: str) -> list[str]:
    text = maybe_decode_base64(text)
    return [m.group(1).strip().rstrip(".,;") for m in URI_RE.finditer(text)]


def valid_uri(uri: str) -> bool:
    try:
        p = urlsplit(uri)
        scheme = p.scheme.lower()
        if scheme not in SCHEMES:
            return False
        if scheme == "vmess":
            raw = (p.netloc + p.path).strip()
            raw += "=" * (-len(raw) % 4)
            obj = json.loads(base64.b64decode(raw.replace("-", "+").replace("_", "/")).decode())
            return bool(obj.get("add") and obj.get("port") and obj.get("id"))
        if not p.hostname or p.port is None or not 1 <= p.port <= 65535:
            return False
        if scheme == "vless":
            uuid.UUID(unquote(p.username or ""))
        elif scheme in {"trojan", "ss", "socks", "socks5"} and not (p.username or p.password):
            return False
        return True
    except (ValueError, UnicodeError, binascii.Error, json.JSONDecodeError):
        return False


async def collect_nodes(*, timeout: float = 15, max_per_source: int = 2000, max_total: int = 2500):
    headers = {"User-Agent": "Neyra/1.0 subscription-builder"}
    limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
    async with httpx.AsyncClient(headers=headers, timeout=httpx.Timeout(timeout), follow_redirects=True, limits=limits) as client:
        async def fetch(url: str):
            try:
                r = await client.get(url)
                r.raise_for_status()
                return r.text, None
            except Exception as exc:
                return None, exc

        results = await asyncio.gather(*(fetch(url) for url in SOURCES))

    unique: dict[str, Node] = {}
    stats: dict[str, dict] = {}
    for source, (text, error) in zip(SOURCES, results):
        if error:
            stats[source] = {"ok": False, "nodes": 0, "error": type(error).__name__}
            continue
        count = 0
        for uri in extract_uris(text or ""):
            if valid_uri(uri):
                key = uri.lower()
                unique.setdefault(key, Node(uri=uri, scheme=urlsplit(uri).scheme.lower(), source=source))
                count += 1
                if count >= max_per_source:
                    break
        stats[source] = {"ok": True, "nodes": count}
    return list(unique.values())[:max_total], stats
