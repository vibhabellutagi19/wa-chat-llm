"""Application settings and configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration settings."""

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # LLM Parameters
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "500"))

    # Conversation Settings
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

    # PostgreSQL Database Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "whatsapp_bot")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")

    # Storage Backend ('memory' or 'database')
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "database")

    @classmethod
    def validate(cls) -> bool:
        """Validate required settings are present."""
        required = [
            cls.TWILIO_ACCOUNT_SID,
            cls.TWILIO_AUTH_TOKEN,
            cls.TWILIO_WHATSAPP_NUMBER,
            cls.OPENAI_API_KEY,
        ]

        # If using database backend, validate DB settings
        if cls.STORAGE_BACKEND == "database":
            required.extend([
                cls.POSTGRES_HOST,
                cls.POSTGRES_DB,
                cls.POSTGRES_USER,
                cls.POSTGRES_PASSWORD,
            ])

        return all(required)


settings = Settings()
