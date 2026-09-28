import os
import ssl
import sys
import urllib.request
from pathlib import Path

import certifi

ROOT_CA = "https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt"
SUB_CA = "https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt"
CERT_DIR = Path(os.getenv("CERT_DIR", "/tmp/max-bot-certs"))


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "max-deepseek-tutor/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    if b"BEGIN CERTIFICATE" not in data:
        raise RuntimeError(f"Downloaded content is not a PEM certificate: {url}")
    return data if data.endswith(b"\n") else data + b"\n"


def prepare_ca_bundle() -> Path:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    standard = Path(certifi.where()).read_bytes()
    if not standard.endswith(b"\n"):
        standard += b"\n"

    russian = _download(ROOT_CA) + _download(SUB_CA)
    combined_path = CERT_DIR / "ca-bundle.crt"
    combined_path.write_bytes(standard + russian)

    os.environ["SSL_CERT_FILE"] = str(combined_path)
    os.environ["REQUESTS_CA_BUNDLE"] = str(combined_path)
    os.environ["CURL_CA_BUNDLE"] = str(combined_path)

    # Validate that Python can load the resulting bundle.
    ssl.create_default_context(cafile=str(combined_path))
    return combined_path


def main() -> None:
    try:
        bundle = prepare_ca_bundle()
        print(f"[startup] Combined CA bundle ready: {bundle}", flush=True)
    except Exception as exc:
        print(f"[startup] WARNING: could not prepare Russian Trusted CA bundle: {exc!r}", flush=True)
        print("[startup] Continuing with default certificate store.", flush=True)

    port = os.getenv("PORT", "8000")
    os.execvp(
        "uvicorn",
        [
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
        ],
    )


if __name__ == "__main__":
    main()
