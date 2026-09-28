from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bothost-provided domain, if "Use domain" is enabled in the panel.
    domain: str = ""

    max_bot_token: str = ""
    max_webhook_secret: str = ""
    max_webhook_url: str = ""
    max_api_base: str = "https://platform-api2.max.ru"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    max_reply_format: str = "markdown"
    max_output_chunk: int = 3900
    history_messages: int = 12
    image_detail: str = "original"
    log_level: str = "INFO"

    @property
    def effective_webhook_url(self) -> str:
        # On Bothost prefer the real DOMAIN supplied by the platform.
        # This avoids guessing a hostname from BOT_ID.
        if self.domain:
            host = self.domain.strip().removeprefix("https://").removeprefix("http://").rstrip("/")
            return f"https://{host}/webhook"
        return self.max_webhook_url.strip()

    def validate_runtime(self) -> None:
        missing = []
        if not self.max_bot_token:
            missing.append("MAX_BOT_TOKEN")
        if not self.deepseek_api_key:
            missing.append("DEEPSEEK_API_KEY")
        if missing:
            raise RuntimeError("Missing required environment variables: " + ", ".join(missing))


settings = Settings()
