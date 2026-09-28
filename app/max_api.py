import asyncio
from typing import Any, Dict

import httpx

from .config import settings
from .ssl_utils import create_ssl_context
from .utils import split_text


class MaxApiClient:
    def __init__(self):
        self.base_url = settings.max_api_base.rstrip("/")
        self.headers = {"Authorization": settings.max_bot_token}

    async def get_me(self) -> dict:
        async with httpx.AsyncClient(timeout=30, verify=create_ssl_context()) as client:
            r = await client.get(f"{self.base_url}/me", headers=self.headers)
            r.raise_for_status()
            return r.json()

    async def get_subscriptions(self) -> dict:
        async with httpx.AsyncClient(timeout=30, verify=create_ssl_context()) as client:
            r = await client.get(f"{self.base_url}/subscriptions", headers=self.headers)
            r.raise_for_status()
            return r.json()

    async def send_text(self, target_kind: str, target_id: int, text: str) -> None:
        chunks = split_text(text, settings.max_output_chunk)
        async with httpx.AsyncClient(timeout=30, verify=create_ssl_context()) as client:
            for i, chunk in enumerate(chunks):
                params = {target_kind: target_id, "disable_link_preview": True}
                body = {
                    "text": chunk,
                    "format": settings.max_reply_format,
                    "notify": True,
                }
                r = await client.post(
                    f"{self.base_url}/messages",
                    headers={**self.headers, "Content-Type": "application/json"},
                    params=params,
                    json=body,
                )
                r.raise_for_status()
                if i + 1 < len(chunks):
                    await asyncio.sleep(0.6)

    async def subscribe_webhook(self, url: str, secret: str) -> dict:
        body = {
            "url": url,
            "update_types": ["message_created", "bot_started"],
            "secret": secret,
        }
        async with httpx.AsyncClient(timeout=30, verify=create_ssl_context()) as client:
            r = await client.post(
                f"{self.base_url}/subscriptions",
                headers={**self.headers, "Content-Type": "application/json"},
                json=body,
            )
            r.raise_for_status()
            return r.json()

    async def delete_webhook(self, url: str) -> dict:
        async with httpx.AsyncClient(timeout=30, verify=create_ssl_context()) as client:
            r = await client.delete(
                f"{self.base_url}/subscriptions",
                headers=self.headers,
                params={"url": url},
            )
            r.raise_for_status()
            return r.json()

    async def poll_updates(self, marker: int | None = None) -> dict:
        params: Dict[str, Any] = {
            "limit": 100,
            "timeout": 60,
            "types": "message_created,bot_started",
        }
        if marker is not None:
            params["marker"] = marker
        async with httpx.AsyncClient(timeout=75, verify=create_ssl_context()) as client:
            r = await client.get(f"{self.base_url}/updates", headers=self.headers, params=params)
            r.raise_for_status()
            return r.json()
