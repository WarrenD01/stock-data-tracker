# Alpaca stock tracker

Local Python CLI that tracks a watchlist in SQLite, snapshots daily closes from Alpaca after the US cash session, and emails a morning report with percent change and charts.

There is no web UI. Add and remove tickers from the command line; keep `python -m tracker run` alive so the scheduler can fire.

## Setup

1. Create a virtualenv and install the package (this puts `src/` on the import path):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

   On macOS/Linux use `source .venv/bin/activate` instead of `.venv\Scripts\activate`.

2. Copy `.env.example` to `.env` and fill in keys.

### Alpaca

Create paper or live API keys at [Alpaca](https://alpaca.markets/). Set `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`.

`ALPACA_DATA_FEED` defaults to `iex` (free/paper). Set `sip` only if your account is entitled to SIP.

### SendGrid

Use a [verified sender](https://docs.sendgrid.com/ui/sending-email/sender-verification) for `EMAIL_FROM`. Set `SENDGRID_API_KEY` and `EMAIL_TO` (the inbox that should receive the 8am Eastern report).

### Database

`DATABASE_PATH` defaults to `data/tracker.db` (created under the project root). The `data/` directory is gitignored.

## Commands

```text
python -m tracker add AAPL
python -m tracker remove AAPL
python -m tracker list
python -m tracker snapshot   # manual close pull
python -m tracker email      # send report now
python -m tracker run        # scheduler (keep process alive)
```

`run` must stay up for weekday 4:05pm Eastern snapshots and the daily 8:00am Eastern email. On Windows you can later wrap that process with Task Scheduler if you do not want a terminal open.

Times use `America/New_York` so daylight saving is correct. User-facing copy can still say “8am Eastern.”
