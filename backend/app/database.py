"""Конфигурация подключения к целевой базе PostgreSQL."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "fefo_optimization_db"),
            user=os.getenv("DB_USER", "fefo_user"),
            password=os.getenv("DB_PASSWORD", "fefo_demo_password"),
        )


@contextmanager
def get_postgres_connection() -> Generator:
    """Открывает соединение с PostgreSQL для будущей реализации репозиториев."""
    import psycopg2

    settings = DatabaseSettings.from_environment()
    connection = psycopg2.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
