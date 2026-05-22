import os
from urllib.parse import urlparse

import mysql.connector


def _config_from_database_url(database_url: str) -> dict:
    parsed = urlparse(database_url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
    }


def _get_db_config() -> dict:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        config = _config_from_database_url(database_url)
    else:
        config = {
            "host": os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306")),
            "user": os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", "root"),
            "database": os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "log_monitor"),
        }

    ssl_ca = os.getenv("MYSQL_SSL_CA") or os.getenv("DB_SSL_CA")
    if ssl_ca:
        config["ssl_ca"] = ssl_ca

    return config


def get_connection():
    return mysql.connector.connect(**_get_db_config())
