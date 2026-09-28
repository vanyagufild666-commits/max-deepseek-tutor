import asyncio
import logging

from app.config import settings
from app.handler import BotHandler
from app.max_api import MaxApiClient

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
log = logging.getLogger("polling")


async def main() -> None:
    settings.validate_runtime()
    api = MaxApiClient()
    handler = BotHandler()

    me = await api.get_me()
    log.info("MAX auth OK. Started as @%s (id=%s)", me.get("username"), me.get("user_id"))

    subs = await api.get_subscriptions()
    active = subs.get("subscriptions") or []
    if active:
        for item in active:
            url = item.get("url")
            if not url:
                continue
            try:
                result = await api.delete_webhook(url)
                log.info("Removed webhook before Long Polling: %s -> %s", url, result)
            except Exception:
                log.exception("Failed to remove webhook %s", url)
                raise

    log.info("Long Polling started.")

    marker = None
    while True:
        try:
            page = await api.poll_updates(marker)
            updates = page.get("updates", [])
            if updates:
                log.info("Received %d update(s)", len(updates))
            for update in updates:
                await handler.handle_update(update)
            if page.get("marker") is not None:
                marker = page["marker"]
        except Exception:
            log.exception("Polling error; retrying in 3 seconds")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
