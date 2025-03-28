from typing import Annotated, Any

from pydantic import BeforeValidator, HttpUrl, SecretStr, TypeAdapter, computed_field
from pydantic_settings import BaseSettings

from schema.models import (
    AllModelEnum,
    OpenAIModelName,
    Provider,
)


def check_str_is_http(x: str) -> str:
    http_url_adapter = TypeAdapter(HttpUrl)
    return str(http_url_adapter.validate_python(x))


class Settings(BaseSettings):
    MODE: str | None = None

    HOST: str = "0.0.0.0"
    PORT: int = 8081

    AUTH_SECRET: SecretStr | None = None

    OPENAI_API_KEY: SecretStr | None = None


    # If DEFAULT_MODEL is None, it will be set in model_post_init
    DEFAULT_MODEL: AllModelEnum | None = None  # type: ignore[assignment]
    AVAILABLE_MODELS: set[AllModelEnum] = set()  # type: ignore[assignment]

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_DB_PATH: str = "logs/logs.db"

    def model_post_init(self, __context: Any) -> None:
        api_keys = {
            Provider.OPENAI: self.OPENAI_API_KEY
        }
        active_keys = [k for k, v in api_keys.items() if v]
        if not active_keys:
            raise ValueError("At least one LLM API key must be provided.")

        for provider in active_keys:
            match provider:
                case Provider.OPENAI:
                    if self.DEFAULT_MODEL is None:
                        self.DEFAULT_MODEL = OpenAIModelName.GPT_4O_MINI
                    self.AVAILABLE_MODELS.update(set(OpenAIModelName))


    @computed_field
    @property
    def BASE_URL(self) -> str:
        return f"http://{self.HOST}:{self.PORT}"

    def is_dev(self) -> bool:
        return self.MODE == "dev"


settings = Settings()
