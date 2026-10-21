from __future__ import annotations

import argparse


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
    parser.exit(2, f"command {args.command!r} is not implemented yet\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
