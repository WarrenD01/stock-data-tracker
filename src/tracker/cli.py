from __future__ import annotations

import argparse

from tracker.emailer import send_morning_report
from tracker.prices import (
    add_ticker,
    list_active_tickers,
    record_close_snapshot,
    remove_ticker,
)
from tracker.scheduler import run_scheduler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracker", description="Alpaca stock tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a ticker to track")
    add_parser.add_argument("symbol", help="Stock symbol, e.g. AAPL")

    remove_parser = subparsers.add_parser("remove", help="Stop tracking a ticker")
    remove_parser.add_argument("symbol", help="Stock symbol, e.g. AAPL")

    subparsers.add_parser("list", help="List tracked tickers")
    subparsers.add_parser("snapshot", help="Pull today's market-close snapshot now")
    subparsers.add_parser("email", help="Send the morning report now")
    subparsers.add_parser("run", help="Run the scheduler until interrupted")

    args = parser.parse_args(argv)

    if args.command == "add":
        symbol, changed = add_ticker(args.symbol)
        if changed:
            print(f"Now tracking {symbol}.")
        else:
            print(f"{symbol} is already being tracked.")
        return 0

    if args.command == "remove":
        removed = remove_ticker(args.symbol)
        if removed:
            print(f"Stopped tracking {args.symbol.strip().upper()}.")
            return 0
        print(f"Ticker {args.symbol.strip().upper()} is not currently tracked.")
        return 1

    if args.command == "list":
        tickers = list_active_tickers()
        if not tickers:
            print("No active tickers tracked.")
        else:
            for sym in tickers:
                print(sym)
        return 0

    if args.command == "snapshot":
        recorded = record_close_snapshot(force=True)
        if not recorded:
            print("No active tickers to snapshot (or no bar data returned).")
        else:
            for sym, price in recorded.items():
                print(f"{sym}: ${price:.2f}")
        return 0

    if args.command == "email":
        sent = send_morning_report()
        if sent:
            print("Morning report sent.")
            return 0
        print("No stored price data found for active tickers; run `snapshot` first.")
        return 1

    if args.command == "run":
        run_scheduler()
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())