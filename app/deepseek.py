from typing import List

import httpx

from .config import settings
from .prompts import SYSTEM_PROMPT


class DeepSeekClient:
    def __init__(self):
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.api_key = settings.deepseek_api_key
        self.model = settings.deepseek_model

    async def answer(self, history: List[dict], text: str, image_data_urls: List[str]) -> str:
        user_content: list[dict] = []
        user_content.append({"type": "text", "text": text or "Проанализируй изображение и ответь на вопрос/реши задачу."})
        for data_url in image_data_urls:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url, "detail": settings.image_detail},
                }
            )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.35,
            "max_tokens": 5000,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise RuntimeError(f"Unexpected DeepSeek response: {data}") from exc
