from __future__ import annotations

import base64

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    ContentId,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)

from tracker.charts import render_ticker_chart_png
from tracker.config import get_settings
from tracker.prices import TickerSummary, get_morning_summaries


def _format_pct(pct: float | None) -> tuple[str, str]:
    if pct is None:
        return "N/A (1st day)", "#6b7280"
    sign = "+" if pct >= 0 else ""
    color = "#16a34a" if pct >= 0 else "#dc2626"
    return f"{sign}{pct:.2f}%", color


def build_email_html(summaries: list[TickerSummary]) -> str:
    rows_html = []
    img_sections = []

    for s in summaries:
        pct_val = float(s.pct_change) if s.pct_change is not None else None
        pct_str, color = _format_pct(pct_val)
        prior_str = f"${s.prior_close:.2f}" if s.prior_close is not None else "—"

        rows_html.append(
            f"<tr>"
            f"<td style='padding:8px;border:1px solid #d1d5db;font-weight:bold;'>{s.symbol}</td>"
            f"<td style='padding:8px;border:1px solid #d1d5db;'>{s.as_of_date.isoformat()}</td>"
            f"<td style='padding:8px;border:1px solid #d1d5db;'>${s.latest_close:.2f}</td>"
            f"<td style='padding:8px;border:1px solid #d1d5db;'>{prior_str}</td>"
            f"<td style='padding:8px;border:1px solid #d1d5db;color:{color};font-weight:bold;'>{pct_str}</td>"
            f"</tr>"
        )
        cid = f"chart_{s.symbol.lower()}"
        img_sections.append(
            f"<div style='margin-top:16px;'>"
            f"<h4 style='margin:0 0 6px 0;font-family:sans-serif;'>{s.symbol} Performance History</h4>"
            f"<img src='cid:{cid}' alt='{s.symbol} chart' style='max-width:600px;border:1px solid #e5e7eb;'/>"
            f"</div>"
        )

    table_body = "\n".join(rows_html)
    charts_body = "\n".join(img_sections)

    return f"""
    <html>
      <body style="font-family:Arial,sans-serif;color:#111827;">
        <h2>Daily Stock Performance Report</h2>
        <table style="border-collapse:collapse;width:100%;max-width:640px;">
          <thead>
            <tr style="background:#f3f4f6;text-align:left;">
              <th style="padding:8px;border:1px solid #d1d5db;">Symbol</th>
              <th style="padding:8px;border:1px solid #d1d5db;">Close Date</th>
              <th style="padding:8px;border:1px solid #d1d5db;">Close Price</th>
              <th style="padding:8px;border:1px solid #d1d5db;">Prior Close</th>
              <th style="padding:8px;border:1px solid #d1d5db;">Daily Change</th>
            </tr>
          </thead>
          <tbody>
            {table_body}
          </tbody>
        </table>
        {charts_body}
      </body>
    </html>
    """


def send_morning_report() -> bool:
    """Generate and send the morning performance email with chart attachments."""
    settings = get_settings()
    if not settings.sendgrid_api_key or not settings.email_from or not settings.email_to:
        raise RuntimeError("SENDGRID_API_KEY, EMAIL_FROM, and EMAIL_TO must be set in .env")

    summaries = get_morning_summaries()
    if not summaries:
        return False

    html_content = build_email_html(summaries)
    message = Mail(
        from_email=settings.email_from,
        to_emails=settings.email_to,
        subject="Morning Stock Tracker Report",
        html_content=html_content,
    )

    for s in summaries:
        png_bytes = render_ticker_chart_png(s)
        encoded = base64.b64encode(png_bytes).decode("ascii")
        attachment = Attachment(
            FileContent(encoded),
            FileName(f"{s.symbol}_history.png"),
            FileType("image/png"),
            Disposition("inline"),
            ContentId(f"chart_{s.symbol.lower()}"),
        )
        message.add_attachment(attachment)

    sg = SendGridAPIClient(settings.sendgrid_api_key)
    response = sg.send(message)
    return 200 <= response.status_code < 300