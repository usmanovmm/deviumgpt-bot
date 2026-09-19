import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    telegram_token: str
    gemini_api_key: str
    port: int = 8080

    @classmethod
    from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        gemini_key = os.getenv("GEMINI_API_KEY")

        if not token or not gemini_key:
            raise RuntimeError(
                "Critical configuration error: TELEGRAM_BOT_TOKEN or GEMINI_API_KEY environment variable is missing."
            )

        return cls(
            telegram_token=token,
            gemini_api_key=gemini_key,
            port=int(os.getenv("PORT", 8080)),
        )
