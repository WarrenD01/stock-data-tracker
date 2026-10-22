from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetCalendarRequest

from tracker.config import get_settings

ET = ZoneInfo("America/New_York")


def _validate_credentials() -> tuple[str, str, DataFeed]:
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        raise RuntimeError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")
    feed = DataFeed(settings.alpaca_data_feed)
    return settings.alpaca_api_key, settings.alpaca_secret_key, feed


def is_trading_day(target_date: date | None = None) -> bool:
    """Return True if the NYSE/NASDAQ market is open on target_date (defaults to today in ET)."""
    api_key, secret_key, _ = _validate_credentials()
    check_date = target_date or datetime.now(ET).date()
    client = TradingClient(api_key, secret_key, paper=True)
    calendar = client.get_calendar(GetCalendarRequest(start=check_date, end=check_date))
    return len(calendar) > 0


def fetch_recent_daily_closes(
    symbols: list[str],
    lookback_calendar_days: int = 7,
) -> dict[str, list[tuple[date, Decimal]]]:
    """Fetch the most recent daily closes (up to last 2 trading sessions) per symbol."""
    if not symbols:
        return {}
    api_key, secret_key, feed = _validate_credentials()
    client = StockHistoricalDataClient(api_key, secret_key)

    end_dt = datetime.now(ET)
    start_dt = end_dt - timedelta(days=lookback_calendar_days)

    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start_dt,
        end=end_dt,
        feed=feed,
    )
    bars_response = client.get_stock_bars(request)

    result: dict[str, list[tuple[date, Decimal]]] = {}
    for sym in symbols:
        sym_bars = bars_response.data.get(sym, [])
        sorted_bars = sorted(sym_bars, key=lambda b: b.timestamp)
        # Keep the last 2 trading days so prior-day % change works immediately
        recent_two = sorted_bars[-2:]
        result[sym] = [
            (bar.timestamp.astimezone(ET).date(), Decimal(str(bar.close)))
            for bar in recent_two
        ]
    return result
