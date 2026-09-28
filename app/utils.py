import base64
import io
from typing import List, Tuple

import httpx
from PIL import Image

from .ssl_utils import create_ssl_context

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


SUPPORTED_DS_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def split_text(text: str, max_len: int = 3900) -> List[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    chunks: List[str] = []
    rest = text
    while rest:
        if len(rest) <= max_len:
            chunks.append(rest)
            break
        cut = rest.rfind("\n\n", 0, max_len)
        if cut < max_len // 2:
            cut = rest.rfind("\n", 0, max_len)
        if cut < max_len // 2:
            cut = rest.rfind(". ", 0, max_len)
            if cut != -1:
                cut += 1
        if cut < max_len // 2:
            cut = rest.rfind(" ", 0, max_len)
        if cut < max_len // 2:
            cut = max_len
        chunks.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    return [c for c in chunks if c]


def extract_image_urls(message: dict) -> List[str]:
    body = message.get("body") or {}
    attachments = body.get("attachments") or []
    urls: List[str] = []
    for attachment in attachments:
        if attachment.get("type") != "image":
            continue
        payload = attachment.get("payload") or {}
        url = payload.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            urls.append(url)
    return urls


def get_message_text(message: dict) -> str:
    body = message.get("body") or {}
    return (body.get("text") or "").strip()


def get_sender_id(message: dict) -> int | None:
    sender = message.get("sender") or {}
    uid = sender.get("user_id")
    return int(uid) if uid is not None else None


def get_target(message: dict) -> Tuple[str, int] | None:
    recipient = message.get("recipient") or {}
    chat_type = recipient.get("chat_type")
    chat_id = recipient.get("chat_id")
    user_id = recipient.get("user_id")
    sender_id = get_sender_id(message)

    if chat_type == "dialog" and sender_id is not None:
        return ("user_id", sender_id)
    if chat_id is not None:
        return ("chat_id", int(chat_id))
    if user_id is not None:
        return ("user_id", int(user_id))
    return None


async def image_url_to_data_url(url: str, auth_token: str | None = None) -> str:
    headers = {}
    if auth_token:
        headers["Authorization"] = auth_token
    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        verify=create_ssl_context(),
    ) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        raw = response.content
        content_type = (response.headers.get("content-type") or "").split(";", 1)[0].strip().lower()

    if content_type in SUPPORTED_DS_MIME:
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

    with Image.open(io.BytesIO(raw)) as img:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=92)
    encoded = base64.b64encode(out.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
