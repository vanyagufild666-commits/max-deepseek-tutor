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
    log.info("Started as @%s (id=%s)", me.get("username"), me.get("user_id"))

    marker = None
    while True:
        try:
            page = await api.poll_updates(marker)
            for update in page.get("updates", []):
                await handler.handle_update(update)
            if page.get("marker") is not None:
                marker = page["marker"]
        except Exception:
            log.exception("Polling error; retrying in 3 seconds")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
