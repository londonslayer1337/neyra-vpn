from __future__ import annotations

import asyncio
import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from app.services.collector import SOURCES, collect_nodes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "sub"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def score_node(node) -> int:
    """Quality heuristic only; no claim of real-world reachability."""
    uri = node.uri
    p = urlsplit(uri)
    q = parse_qs(p.query)
    score = 0
    if node.scheme == "vless":
        score += 40
        if q.get("security", [""])[0].lower() in {"reality", "tls"}:
            score += 25
        if q.get("type", [""])[0].lower() in {"tcp", "ws", "grpc"}:
            score += 10
        if q.get("flow", [""])[0]:
            score += 5
        if q.get("sni", [""])[0]:
            score += 5
        if q.get("fp", [""])[0]:
            score += 5
    elif node.scheme == "trojan":
        score += 32
        if q.get("security", [""])[0].lower() == "tls":
            score += 15
    elif node.scheme in {"hysteria2", "hy2", "tuic"}:
        score += 30
    elif node.scheme == "vmess":
        score += 20
    else:
        score += 10
    host = (p.hostname or "").lower()
    if host and not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        score += 5
    if p.port in {443, 8443, 2053, 2083, 2087, 2096}:
        score += 3
    return score


def build_body(nodes: list, title: str, limit: int) -> str:
    ranked = sorted(nodes, key=lambda n: (-score_node(n), n.uri))[:limit]
    lines = [
        "#profile-title: " + title,
        "#profile-update-interval: 4",
        "#subscription-auto-update-enable: 1",
        "#subscription-auto-update-open-enable: 1",
        "#subscription-ping-onopen-enabled: 1",
    ]
    lines.extend(n.uri for n in ranked)
    return "\n".join(lines) + "\n"


async def main() -> None:
    min_nodes = int(os.getenv("NEYRA_MIN_NODES", "5"))
    best_limit = int(os.getenv("NEYRA_BEST_NODES", "50"))
    creator_limit = int(os.getenv("NEYRA_CREATOR_NODES", "100"))
    nodes, source_stats = await collect_nodes()
    if len(nodes) < min_nodes:
        raise SystemExit(f"Refusing weak build: {len(nodes)} nodes < {min_nodes}")

    public_body = build_body(nodes, "Neyra Basic", len(nodes))
    best_body = build_body(nodes, "Neyra Best", best_limit)
    creator_body = build_body(nodes, "Neyra Creator", creator_limit)

    write(OUT / "public.txt", base64.b64encode(public_body.encode()).decode() + "\n")
    write(OUT / "best.txt", base64.b64encode(best_body.encode()).decode() + "\n")
    write(OUT / "creator.txt", base64.b64encode(creator_body.encode()).decode() + "\n")
    write(OUT / "plain.txt", public_body)
    schemes = {s: sum(n.scheme == s for n in nodes) for s in sorted({n.scheme for n in nodes})}
    stats = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nodes": len(nodes),
        "best_nodes": min(len(nodes), best_limit),
        "creator_nodes": min(len(nodes), creator_limit),
        "sources_total": len(SOURCES),
        "sources_ok": sum(1 for s in source_stats.values() if s["ok"]),
        "sources_failed": sum(1 for s in source_stats.values() if not s["ok"]),
        "schemes": schemes,
        "auto_update_hours": 4,
        "source_stats": source_stats,
        "ranking_note": "Quality heuristic; reachability is not guaranteed.",
    }
    write(OUT / "stats.json", json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"nodes": len(nodes), "best": min(len(nodes), best_limit), "creator": min(len(nodes), creator_limit)}))


if __name__ == "__main__":
    asyncio.run(main())
