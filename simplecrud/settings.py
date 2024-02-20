from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    region: str | None = None
    secret_name: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="aws_"
    )


class MySqlSettings(BaseSettings):
    url: str | None = None
    pool_size: int = 3
    max_overflow: int = 10
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="mysql_"
    )


_aws_settings: AWSSettings | None = None
_mysql_settings: MySqlSettings | None = None


def get_aws_settings() -> AWSSettings:
    global _aws_settings
    if _aws_settings is None:
        _aws_settings = AWSSettings()
    return _aws_settings


def get_mysql_settings() -> MySqlSettings:
    global _mysql_settings
    if _mysql_settings is None:
        _mysql_settings = MySqlSettings()
    return _mysql_settings
