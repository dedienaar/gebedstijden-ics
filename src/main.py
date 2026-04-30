from __future__ import annotations

from pathlib import Path

import httpx

from calendar_builder import CalendarBuilder, IcsWriter
from fetcher import PageFetcher
from parser import HissaMonthParser

URL = 'https://www.hissa.nl/his/maand'
CACHE_PATH = Path('.tmp/hissa_month.html')
OUTPUT_PATH = Path('export/prayer_times.ics')


def main() -> None:
    # --- Fetch ---
    with httpx.Client(timeout=10.0) as client:
        fetcher = PageFetcher(
            client=client,
            url=URL,
            cache_path=CACHE_PATH,
            ttl_seconds=6 * 3600,
        )

        html_path = fetcher.fetch()

    # --- Parse ---
    html = html_path.read_text(encoding='utf-8')

    parser = HissaMonthParser()
    days = parser.parse(html)

    if not days:
        raise RuntimeError('No prayer days parsed — aborting to avoid empty ICS output')

    # --- Build calendar ---
    calendar_builder = CalendarBuilder()

    calendar_builder.add_events(days)

    calendar_builder.add_metadata('PRODID', '-//Hissa Prayer Calendar//NL//EN')
    calendar_builder.add_metadata('X-WR-CALNAME', 'Prayer Times')
    calendar_builder.add_metadata('X-WR-CALDESC', 'Daily prayer times from Hissa')
    calendar_builder.add_metadata('X-WR-TIMEZONE', 'Europe/Amsterdam')
    calendar_builder.add_metadata('X-PUBLISHED-TTL', 'PT12H')

    result = calendar_builder.build()

    # --- Write ICS ---
    writer = IcsWriter(OUTPUT_PATH)
    writer.write(result.calendar)

    print(f'Generated {len(result.events)} events → {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
