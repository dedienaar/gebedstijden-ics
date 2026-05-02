from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event, vDatetime

from models import PrayerDay


def generate_uid(event_date: date, event_name: str) -> str:
    raw = f'{event_date.isoformat()}|{event_name.casefold()}'
    return hashlib.blake2b(raw.encode(), digest_size=16).hexdigest()


def to_datetime(event_date: date, time_str: str, tz: ZoneInfo) -> datetime:
    hour, minute = map(int, time_str.split(':'))
    return datetime(
        event_date.year,
        event_date.month,
        event_date.day,
        hour,
        minute,
        tzinfo=tz,
    )


class EventStrategy(Protocol):
    def events_for(self, day: PrayerDay) -> list[tuple[str, str]]: ...


class PrayerEventStrategy:
    def events_for(self, day: PrayerDay) -> list[tuple[str, str]]:
        return [
            ('🌃 Fajr', day.fajr),
            ('🌅 Sunrise', day.sunrise),
            ('🏙️ Dhuhr', day.dhuhr),
            ('🌆 Asr', day.asr),
            ('🌄 Maghrib', day.maghrib),
            ('🌌 Isha', day.isha),
        ]


@dataclass(frozen=True)
class CalendarEvent:
    uid: str
    name: str
    begin: datetime
    end: datetime
    description: str = ''


@dataclass(frozen=True)
class BuildResult:
    calendar: Calendar
    events: list[CalendarEvent]


class CalendarBuilder:
    def __init__(
        self,
        event_strategy: EventStrategy = PrayerEventStrategy(),
        timezone: str = 'Europe/Amsterdam',
        duration_minutes: int = 10,
    ) -> None:
        self._strategy = event_strategy
        self._tz = ZoneInfo(timezone)
        self._duration = timedelta(minutes=duration_minutes)
        self._calendar = Calendar()
        self._calendar.add('version', '2.0')
        self._metadata: dict[str, str] = {}
        self._events: list[CalendarEvent] = []

    def build(self) -> BuildResult:
        for key, value in self._metadata.items():
            self._calendar[key] = value
        return BuildResult(calendar=self._calendar, events=self._events)

    def add_events(self, days: list[PrayerDay]) -> None:
        for day in days:
            for name, time_str in self._strategy.events_for(day):
                self._add_event(day.date, name, time_str)

    def add_metadata(self, key: str, value: str) -> None:
        self._metadata[key] = value

    def _add_event(self, event_date: date, name: str, time_str: str) -> None:
        begin = to_datetime(event_date, time_str, self._tz)
        end = begin + self._duration

        event = Event()
        uid = generate_uid(event_date, name)
        event['uid'] = uid
        event['summary'] = name
        event['dtstart'] = vDatetime(begin)
        event['dtend'] = vDatetime(end)

        self._calendar.add_component(event)
        self._events.append(
            CalendarEvent(
                uid=uid,
                name=name,
                begin=begin,
                end=end,
            )
        )


class IcsWriter:
    """Writes an iCalendar object to a file using atomic writes."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def write(self, calendar: Calendar) -> Path:
        """Write calendar to file atomically.

        Args:
            calendar: The Calendar object to write

        Returns:
            Path to the written file
        """
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            mode='wb',
            dir=self._output_path.parent,
            delete=False,
        ) as tmp_file:
            tmp_file.write(calendar.to_ical())
            tmp_path = Path(tmp_file.name)

        tmp_path.replace(self._output_path)
        return self._output_path
