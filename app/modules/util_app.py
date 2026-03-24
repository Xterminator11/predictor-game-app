from pydantic_settings import SettingsConfigDict
import os


def get_bucket_name():
    """Function to get the bucket name from the .env file using pydantic settings."""

    class Settings:
        """Pydantic settings class to load environment variables."""

        model_config = SettingsConfigDict(
            env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        )

        BUCKET_NAME: str

    settings = Settings()
    return settings.BUCKET_NAME
