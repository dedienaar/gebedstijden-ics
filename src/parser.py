from __future__ import annotations

from datetime import date

from selectolax.parser import HTMLParser

from models import PrayerDay


class HissaMonthParser:
    def parse(self, html: str) -> list[PrayerDay]:
        tree = HTMLParser(html)

        year = self._extract_year(tree)

        rows = tree.css('tr')

        days: list[PrayerDay] = []

        current_year = year
        previous_month: int | None = None

        for row in rows:
            anchor = row.css_first('a[id]')
            if not anchor:
                continue

            anchor_id = anchor.attributes.get('id')
            if not anchor_id or len(anchor_id) != 4 or not anchor_id.isdigit():
                continue

            month = int(anchor_id[:2])
            day = int(anchor_id[2:])

            # detect year rollover
            if previous_month is not None and month < previous_month:
                current_year += 1

            previous_month = month

            cells = row.css('td')
            if len(cells) < 8:
                continue

            try:
                fajr = cells[7].text(strip=True)
                sunrise = cells[6].text(strip=True)
                dhuhr = cells[5].text(strip=True)
                asr = cells[4].text(strip=True)
                maghrib = cells[3].text(strip=True)
                isha = cells[2].text(strip=True)
            except IndexError:
                continue

            days.append(
                PrayerDay(
                    date=date(current_year, month, day),
                    fajr=fajr,
                    sunrise=sunrise,
                    dhuhr=dhuhr,
                    asr=asr,
                    maghrib=maghrib,
                    isha=isha,
                )
            )

        return days

    def _extract_year(self, tree: HTMLParser) -> int:
        for cell in tree.css('td'):
            text = cell.text(separator=' ', strip=True)
            if text and text[:4].isdigit():
                return int(text[:4])

        raise ValueError('Could not extract year from HTML')
