import asyncio
import logging

from .config import settings
from .deepseek import DeepSeekClient
from .history import ConversationStore
from .max_api import MaxApiClient
from .utils import extract_image_urls, get_message_text, get_sender_id, get_target, image_url_to_data_url

log = logging.getLogger(__name__)


class BotHandler:
    def __init__(self):
        self.max_api = MaxApiClient()
        self.deepseek = DeepSeekClient()
        self.history = ConversationStore(settings.history_messages)
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock_for(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def handle_update(self, update: dict) -> None:
        update_type = update.get("update_type")
        if update_type == "bot_started":
            user = update.get("user") or {}
            user_id = user.get("user_id")
            if user_id is not None:
                await self.max_api.send_text(
                    "user_id",
                    int(user_id),
                    "Привет! Я отвечаю на вопросы и умею разбирать задания по фото. "
                    "Если пришлёшь школьную задачу, дам два полных решения: эталонное и более простое, как у школьника.",
                )
            return

        if update_type != "message_created":
            return

        message = update.get("message") or {}
        sender = message.get("sender") or {}
        if sender.get("is_bot"):
            return

        user_id = get_sender_id(message)
        target = get_target(message)
        if user_id is None or target is None:
            log.warning("Cannot resolve sender or reply target for update: %s", update)
            return

        text = get_message_text(message)
        if text.lower() in {"/reset", "/clear", "сброс", "очистить историю"}:
            self.history.clear(user_id)
            await self.max_api.send_text(*target, "История диалога очищена.")
            return

        image_urls = extract_image_urls(message)
        if not text and not image_urls:
            await self.max_api.send_text(*target, "Пришли текстовый вопрос или изображение с заданием.")
            return

        async with self._lock_for(user_id):
            try:
                image_data_urls = []
                for url in image_urls[:12]:
                    try:
                        data_url = await image_url_to_data_url(url)
                    except Exception:
                        data_url = await image_url_to_data_url(url, auth_token=settings.max_bot_token)
                    image_data_urls.append(data_url)

                history = self.history.get(user_id)
                answer = await self.deepseek.answer(history, text, image_data_urls)
                self.history.append(user_id, "user", text or "[изображение]")
                self.history.append(user_id, "assistant", answer)
                await self.max_api.send_text(*target, answer)
            except Exception as exc:
                log.exception("Failed to handle message")
                await self.max_api.send_text(
                    *target,
                    "Не получилось обработать запрос. Проверь настройки API и попробуй ещё раз. "
                    f"Техническая причина: {type(exc).__name__}",
                )
