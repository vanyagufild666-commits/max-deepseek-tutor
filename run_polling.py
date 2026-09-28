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
        urls = [item.get("url", "<unknown>") for item in active]
        raise RuntimeError(
            "Long Polling cannot run while MAX Webhook subscriptions are active. "
            "Active webhook(s): " + ", ".join(urls)
        )

    log.info("No active webhook subscriptions. Long Polling started.")

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
