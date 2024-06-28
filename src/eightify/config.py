from typing import Optional

from loguru import logger
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler
from rich.traceback import install

install(show_locals=True)


class Settings(BaseSettings):
    llm_model: str = "gpt-4o"
    anthropic_key: SecretStr = ""
    openai_api_key: SecretStr = ""
    youtube_api_key: SecretStr = ""
    min_number_of_comments: int = 10
    max_number_of_comments: int = 100
    max_points: int = 5
    # TODO: default should be some small int to avoid burning API credits relentlessly
    # but .env parsing of "null" into Optional[int] is not working as expected
    max_transcript_length: Optional[int] = None
    log_level: str = "DEBUG"
    log_prompt_length: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()

logger.configure(
    handlers=[
        {
            "sink": RichHandler(markup=True),
            "format": "{message}",
            "level": config.log_level,
        }
    ]
)
