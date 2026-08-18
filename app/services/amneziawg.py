from __future__ import annotations

import base64
import logging
import random

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

log = logging.getLogger(__name__)

API_URL = "https://api.cloudflareclient.com/v0a215/reg"
CLEAN_IPS = [
    "188.114.96.1", "188.114.96.2", "188.114.96.3",
    "188.114.98.1", "188.114.98.2", "188.114.99.1",
    "162.159.192.1", "162.159.195.1", "162.159.196.1",
]


def generate_keys() -> tuple[str, str]:
    private = x25519.X25519PrivateKey.generate()
    public = private.public_key()
    priv = private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    pub = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(priv).decode(), base64.b64encode(pub).decode()


async def register() -> dict:
    private_key, public_key = generate_keys()
    payload = {
        "install_id": "",
        "tos": "2024-01-01T00:00:00.000Z",
        "key": public_key,
        "fcm_token": "",
        "type": "Android",
        "locale": "en_US",
    }
    headers = {"User-Agent": "Neyra/1.0", "Content-Type": "application/json; charset=UTF-8"}
    async with httpx.AsyncClient(http2=True, timeout=12, headers=headers) as client:
        response = await client.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
    result = data.get("result", data)
    config = result.get("config", {})
    interface = config.get("interface", {})
    peers = config.get("peers") or []
    if not interface or not peers:
        raise RuntimeError("Incomplete WARP registration response")
    addresses = interface.get("addresses", {})
    peer = peers[0]
    values = {
        "private_key": private_key,
        "v4_addr": addresses.get("v4"),
        "v6_addr": addresses.get("v6"),
        "peer_pubkey": peer.get("public_key"),
        "endpoint": f"{random.choice(CLEAN_IPS)}:4500",
    }
    if any(not values.get(k) for k in values):
        raise RuntimeError("WARP response missing required fields")
    return values


def build_config(data: dict) -> str:
    return f"""[Interface]\nPrivateKey = {data['private_key']}\nAddress = {data['v4_addr']}, {data['v6_addr']}\nDNS = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111, 2606:4700:4700::1001\nMTU = 1280\nJc = 19\nJmin = 76\nJmax = 322\nS1 = 0\nS2 = 0\nS3 = 0\nS4 = 0\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\n\n[Peer]\nPublicKey = {data['peer_pubkey']}\nAllowedIPs = 0.0.0.0/0\nEndpoint = {data['endpoint']}\nPersistentKeepalive = 25\n"""
