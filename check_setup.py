import asyncio
import json
import sys

import httpx

from app.config import settings
from app.max_api import MaxApiClient


async def check_deepseek() -> None:
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [{"role": "user", "content": "Ответь одним словом: работает"}],
        "max_tokens": 20,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        print(f"DeepSeek HTTP: {r.status_code}")
        if r.is_error:
            print(r.text[:1000])
            r.raise_for_status()
        data = r.json()
        print("DeepSeek answer:", data["choices"][0]["message"]["content"])


async def main() -> None:
    try:
        settings.validate_runtime()
    except Exception as exc:
        print("CONFIG ERROR:", exc)
        sys.exit(1)

    print("MAX API:", settings.max_api_base)
    print("DeepSeek model:", settings.deepseek_model)
    print("MAX token configured:", bool(settings.max_bot_token))
    print("DeepSeek key configured:", bool(settings.deepseek_api_key))
    print()

    api = MaxApiClient()

    try:
        me = await api.get_me()
        print("MAX /me: OK")
        print(json.dumps({
            "user_id": me.get("user_id"),
            "username": me.get("username"),
            "first_name": me.get("first_name"),
        }, ensure_ascii=False))
    except Exception as exc:
        print("MAX /me: FAIL", repr(exc))
        sys.exit(2)

    try:
        subs = await api.get_subscriptions()
        print("\nMAX subscriptions:")
        print(json.dumps(subs, ensure_ascii=False, indent=2))
        active = subs.get("subscriptions") or []
        if active:
            print("\nWARNING: Webhook subscription is active.")
            print("Long Polling via run_polling.py will not work at the same time.")
        else:
            print("\nNo webhook subscriptions. Long Polling can be used for local testing.")
    except Exception as exc:
        print("\nMAX subscriptions check: FAIL", repr(exc))

    print()
    try:
        await check_deepseek()
    except Exception as exc:
        print("DeepSeek check: FAIL", repr(exc))
        sys.exit(3)

    print("\nALL BASIC CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
