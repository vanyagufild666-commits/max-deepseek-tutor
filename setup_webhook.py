import asyncio

from app.config import settings
from app.max_api import MaxApiClient


async def main() -> None:
    settings.validate_runtime()
    if not settings.max_webhook_url:
        raise RuntimeError("Set MAX_WEBHOOK_URL in .env")
    if not settings.max_webhook_secret:
        raise RuntimeError("Set MAX_WEBHOOK_SECRET in .env")

    result = await MaxApiClient().subscribe_webhook(settings.max_webhook_url, settings.max_webhook_secret)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
