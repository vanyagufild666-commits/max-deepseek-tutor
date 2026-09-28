from app.utils import extract_image_urls, get_target, split_text


def test_extract_image_urls():
    message = {
        "body": {
            "attachments": [
                {"type": "image", "payload": {"url": "https://example.com/a.jpg", "token": "x", "photo_id": 1}},
                {"type": "file", "payload": {"url": "https://example.com/a.pdf"}},
            ]
        }
    }
    assert extract_image_urls(message) == ["https://example.com/a.jpg"]


def test_dialog_reply_goes_to_sender():
    message = {
        "sender": {"user_id": 42},
        "recipient": {"chat_type": "dialog", "user_id": 100},
    }
    assert get_target(message) == ("user_id", 42)


def test_split_text():
    text = ("Абзац. " * 1000).strip()
    chunks = split_text(text, 3900)
    assert len(chunks) > 1
    assert all(len(x) <= 3900 for x in chunks)
