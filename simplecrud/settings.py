from pydantic import MySQLDsn
from pydantic_settings import SettingsConfigDict


class MySqlSettings:
    url = "mysql+aiomysql://root:root@localhost:3306/crud_test"  #: MySQLDsn
    pool_size: int = 3
    max_overflow: int = 10
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="mysql_"
    )
