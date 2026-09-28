import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from .config import settings
from .handler import BotHandler

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
app = FastAPI(title="MAX DeepSeek Tutor Bot", version="1.0.0")
handler = BotHandler()


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "max_api": settings.max_api_base,
        "deepseek_model": settings.deepseek_model,
    }


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_max_bot_api_secret: str | None = Header(default=None, alias="X-Max-Bot-Api-Secret"),
) -> dict:
    if settings.max_webhook_secret and x_max_bot_api_secret != settings.max_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    update = await request.json()
    background_tasks.add_task(handler.handle_update, update)
    return {"ok": True}
