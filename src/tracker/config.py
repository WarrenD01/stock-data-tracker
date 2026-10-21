from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_data_feed: str
    sendgrid_api_key: str
    email_from: str
    email_to: str
    database_path: Path


def get_settings() -> Settings:
    database_path = Path(os.getenv("DATABASE_PATH", "data/tracker.db"))
    if not database_path.is_absolute():
        database_path = _PROJECT_ROOT / database_path

    return Settings(
        alpaca_api_key=os.getenv("ALPACA_API_KEY", ""),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", ""),
        alpaca_data_feed=os.getenv("ALPACA_DATA_FEED", "iex").lower(),
        sendgrid_api_key=os.getenv("SENDGRID_API_KEY", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        email_to=os.getenv("EMAIL_TO", ""),
        database_path=database_path,
    )
