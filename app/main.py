import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from .config import settings
from .handler import BotHandler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("max-bot")

app = FastAPI(title="MAX DeepSeek Tutor Bot", version="1.1.0")
handler = BotHandler()


@app.on_event("startup")
async def startup_checks() -> None:
    log.info("Application starting")
    log.info(
        "Config: MAX token=%s, DeepSeek key=%s, webhook URL=%s, webhook secret=%s",
        bool(settings.max_bot_token),
        bool(settings.deepseek_api_key),
        bool(settings.max_webhook_url),
        bool(settings.max_webhook_secret),
    )

    try:
        settings.validate_runtime()
    except Exception:
        log.exception("Configuration validation failed")
        return

    try:
        me = await handler.max_api.get_me()
        log.info(
            "MAX authorization OK: username=%s user_id=%s",
            me.get("username"),
            me.get("user_id"),
        )
    except Exception:
        log.exception("MAX authorization/HTTPS check FAILED")
        return

    try:
        subscriptions = await handler.max_api.get_subscriptions()
        active = subscriptions.get("subscriptions") or []
        urls = [item.get("url") for item in active if item.get("url")]
        log.info("MAX webhook subscriptions: %s", urls or "<none>")

        if settings.max_webhook_url:
            # Re-submit on every startup so URL, event types and secret stay in sync
            # with the current Bothost environment after redeploys.
            result = await handler.max_api.subscribe_webhook(
                settings.max_webhook_url,
                settings.max_webhook_secret,
            )
            log.info(
                "Webhook synchronization result for %s: %s",
                settings.max_webhook_url,
                result,
            )
        else:
            log.warning("MAX_WEBHOOK_URL is empty; MAX cannot deliver webhook events")
    except Exception:
        log.exception("Webhook subscription check/setup FAILED")


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "max_api": settings.max_api_base,
        "deepseek_model": settings.deepseek_model,
        "max_token_configured": bool(settings.max_bot_token),
        "deepseek_key_configured": bool(settings.deepseek_api_key),
        "webhook_url_configured": bool(settings.max_webhook_url),
        "webhook_secret_configured": bool(settings.max_webhook_secret),
    }


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_max_bot_api_secret: str | None = Header(default=None, alias="X-Max-Bot-Api-Secret"),
) -> dict:
    if settings.max_webhook_secret and x_max_bot_api_secret != settings.max_webhook_secret:
        log.warning(
            "Rejected webhook: secret mismatch (header present=%s)",
            bool(x_max_bot_api_secret),
        )
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    update = await request.json()
    log.info(
        "Webhook received: update_type=%s timestamp=%s",
        update.get("update_type"),
        update.get("timestamp"),
    )
    background_tasks.add_task(handler.handle_update, update)
    return {"ok": True}


if __name__ == "__main__":
    import os

    import uvicorn

    try:
        from start import prepare_ca_bundle

        bundle = prepare_ca_bundle()
        log.info("Combined CA bundle ready: %s", bundle)
    except Exception:
        log.exception("Could not prepare Russian Trusted CA bundle; continuing with default trust store")

    port = int(os.getenv("PORT", "8000"))
    log.info("Starting Uvicorn on 0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=settings.log_level.lower())
