from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo

from ics import Calendar, Event

from models import PrayerDay


class UIDGenerator:
    def generate(self, event_date: date, event_name: str) -> str:
        raw = f'{event_date.isoformat()}|{event_name.casefold()}'
        return hashlib.blake2b(raw.encode('utf-8'), digest_size=16).hexdigest()


class CalendarBuilder:
    def __init__(
        self,
        uid_generator: UIDGenerator | None = None,
        timezone: str = 'Europe/Amsterdam',
        duration_minutes: int = 5,
    ) -> None:
        self._uid_generator = uid_generator or UIDGenerator()
        self._tz = ZoneInfo(timezone)
        self._duration = timedelta(minutes=duration_minutes)

    def build(self, days: list[PrayerDay]) -> Calendar:
        calendar = Calendar()

        for day in days:
            for event_name, time_str in self._events_for(day):
                self._add_event(calendar, day.date, event_name, time_str)

        return calendar

    def _events_for(self, day: PrayerDay) -> list[tuple[str, str]]:
        return [
            ('Fajr', day.fajr),
            ('Sunrise', day.sunrise),
            ('Dhuhr', day.dhuhr),
            ('Asr', day.asr),
            ('Maghrib', day.maghrib),
            ('Isha', day.isha),
        ]

    def _add_event(
        self,
        calendar: Calendar,
        event_date: date,
        event_name: str,
        time_str: str,
    ) -> None:
        begin = self._to_datetime(event_date, time_str)

        event = Event()
        event.uid = self._uid_generator.generate(event_date, event_name)
        event.name = event_name
        event.begin = begin
        event.end = begin + self._duration
        event.description = f'{event_name}'

        calendar.events.add(event)

    def _to_datetime(self, event_date: date, time_str: str) -> datetime:
        hour, minute = map(int, time_str.split(':'))
        return datetime(
            event_date.year,
            event_date.month,
            event_date.day,
            hour,
            minute,
            tzinfo=self._tz,
        )


class IcsWriter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def write(self, calendar: Calendar) -> Path:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        ics_text = calendar.serialize()

        with NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=self._output_path.parent,
            delete=False,
        ) as tmp_file:
            tmp_file.write(ics_text)
            tmp_path = Path(tmp_file.name)

        tmp_path.replace(self._output_path)
        return self._output_path
