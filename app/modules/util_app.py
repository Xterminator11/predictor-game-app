from pydantic_settings import SettingsConfigDict, BaseSettings
import os
import boto3
import json


class Settings(BaseSettings):
    """Pydantic settings class to load environment variables."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    )

    BUCKET_NAME: str


def get_bucket_name():
    """Function to get the bucket name from the .env file using pydantic settings."""

    settings = Settings()
    # print(settings.__dict__)
    return settings.BUCKET_NAME


def get_match_details_json(data_type: str = "json"):
    """Function to get match details from S3 as either a JSON string or a pandas DataFrame."""

    if data_type == "json":
        s3 = boto3.client("s3")
        data = s3.get_object(Bucket=get_bucket_name(), Key="matches/match_details.json")

        return data["Body"].read().decode("utf-8")
    elif data_type == "pandas":
        return f"s3://{get_bucket_name()}/matches/match_details.json"
    else:
        raise ValueError("Invalid type. Expected 'json' or 'pandas'.")


def put_match_details_json(match_details: dict):
    """Function to upload match details to S3 as a JSON file."""

    s3 = boto3.client("s3")
    match_details_path = "matches/match_details.json"
    s3.put_object(
        Bucket=get_bucket_name(),
        Key=match_details_path,
        Body=json.dumps(match_details, indent=4),
        ContentType="application/json",
    )
