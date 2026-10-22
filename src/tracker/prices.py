from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select

from tracker.alpaca_client import fetch_recent_daily_closes, is_trading_day
from tracker.db import session_scope
from tracker.models import Price, Ticker

ET = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class TickerSummary:
    symbol: str
    as_of_date: date
    latest_close: Decimal
    prior_close: Decimal | None
    pct_change: Decimal | None
    history_dates: list[date]
    history_closes: list[Decimal]


def _to_et_date(dt: datetime) -> date:
    """Convert a naive-UTC or aware-UTC datetime from SQLite into an Eastern date."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ET).date()


def add_ticker(symbol: str) -> tuple[str, bool]:
    """Add or reactivate a ticker. Returns (normalized_symbol, was_created_or_reactivated)."""
    norm = symbol.strip().upper()
    if not norm:
        raise ValueError("Ticker symbol cannot be empty.")

    with session_scope() as session:
        existing = session.scalar(select(Ticker).where(Ticker.symbol == norm))
        if existing is not None:
            if existing.removed_at is None:
                return existing.symbol, False
            existing.removed_at = None
            existing.added_at = datetime.now(timezone.utc)
            return existing.symbol, True

        ticker = Ticker(symbol=norm)
        session.add(ticker)
        session.flush()
        return ticker.symbol, True


def remove_ticker(symbol: str) -> bool:
    """Soft-delete an active ticker by setting removed_at."""
    norm = symbol.strip().upper()
    with session_scope() as session:
        ticker = session.scalar(
            select(Ticker).where(Ticker.symbol == norm, Ticker.removed_at.is_(None))
        )
        if ticker is None:
            return False
        ticker.removed_at = datetime.now(timezone.utc)
        return True


def list_active_tickers() -> list[str]:
    """Return sorted list of currently tracked ticker symbols."""
    with session_scope() as session:
        stmt = (
            select(Ticker.symbol)
            .where(Ticker.removed_at.is_(None))
            .order_by(Ticker.symbol.asc())
        )
        return list(session.scalars(stmt).all())


def record_close_snapshot(force: bool = False) -> dict[str, Decimal]:
    """Pull latest daily closes from Alpaca for all active tickers and upsert into SQLite."""
    if not force and not is_trading_day():
        return {}

    with session_scope() as session:
        active_tickers = list(
            session.scalars(
                select(Ticker).where(Ticker.removed_at.is_(None)).order_by(Ticker.symbol.asc())
            ).all()
        )
        if not active_tickers:
            return {}

        symbols = [t.symbol for t in active_tickers]
        bars_by_symbol = fetch_recent_daily_closes(symbols)

        latest_recorded: dict[str, Decimal] = {}
        for ticker in active_tickers:
            bars = bars_by_symbol.get(ticker.symbol, [])
            for bar_date, close_price in bars:
                existing_price = session.scalar(
                    select(Price).where(
                        Price.ticker_id == ticker.id,
                        Price.as_of_date == bar_date,
                    )
                )
                if existing_price is None:
                    session.add(
                        Price(
                            ticker_id=ticker.id,
                            as_of_date=bar_date,
                            close=close_price,
                        )
                    )
                else:
                    existing_price.close = close_price
                latest_recorded[ticker.symbol] = close_price

        return latest_recorded


def get_morning_summaries() -> list[TickerSummary]:
    """Build performance summaries and chart series for all active tickers."""
    summaries: list[TickerSummary] = []
    with session_scope() as session:
        active_tickers = list(
            session.scalars(
                select(Ticker).where(Ticker.removed_at.is_(None)).order_by(Ticker.symbol.asc())
            ).all()
        )
        for ticker in active_tickers:
            all_prices = list(
                session.scalars(
                    select(Price)
                    .where(Price.ticker_id == ticker.id)
                    .order_by(Price.as_of_date.asc())
                ).all()
            )
            if not all_prices:
                continue

            latest = all_prices[-1]
            prior = all_prices[-2] if len(all_prices) >= 2 else None
            pct_change: Decimal | None = None
            if prior is not None and prior.close != 0:
                pct_change = ((latest.close - prior.close) / prior.close) * Decimal("100")

            added_date = _to_et_date(ticker.added_at)
            tracked_prices = [p for p in all_prices if p.as_of_date >= added_date] or all_prices[-2:]

            summaries.append(
                TickerSummary(
                    symbol=ticker.symbol,
                    as_of_date=latest.as_of_date,
                    latest_close=latest.close,
                    prior_close=prior.close if prior else None,
                    pct_change=pct_change,
                    history_dates=[p.as_of_date for p in tracked_prices],
                    history_closes=[p.close for p in tracked_prices],
                )
            )
    return summaries
