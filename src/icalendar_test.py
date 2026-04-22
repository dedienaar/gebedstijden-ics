from __future__ import annotations

from datetime import date

import pytest

from icalendar import CalendarBuilder, UIDGenerator
from models import PrayerDay

# --- UID GENERATOR ---


@pytest.mark.parametrize(
    'name',
    ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'],
)
def test_uid_generator_is_deterministic_per_input(name: str):
    generator = UIDGenerator()

    uid1 = generator.generate(date(2026, 4, 20), name)
    uid2 = generator.generate(date(2026, 4, 20), name)

    assert uid1 == uid2


@pytest.mark.parametrize(
    'date1, date2',
    [
        (date(2026, 4, 20), date(2026, 4, 21)),
        (date(2026, 1, 1), date(2026, 12, 31)),
    ],
)
def test_uid_generator_varies_with_date(date1: date, date2: date):
    generator = UIDGenerator()

    uid1 = generator.generate(date1, 'Fajr')
    uid2 = generator.generate(date2, 'Fajr')

    assert uid1 != uid2


@pytest.mark.parametrize(
    'name1, name2',
    [
        ('Fajr', 'Sunrise'),
        ('Dhuhr', 'Asr'),
    ],
)
def test_uid_generator_varies_with_event_name(name1: str, name2: str):
    generator = UIDGenerator()

    uid1 = generator.generate(date(2026, 4, 20), name1)
    uid2 = generator.generate(date(2026, 4, 20), name2)

    assert uid1 != uid2


# --- FIXTURES ---


@pytest.fixture
def day1() -> PrayerDay:
    return PrayerDay(
        date=date(2026, 4, 20),
        fajr='04:20',
        sunrise='06:28',
        dhuhr='13:46',
        asr='17:38',
        maghrib='20:54',
        isha='22:44',
    )


@pytest.fixture
def day2() -> PrayerDay:
    return PrayerDay(
        date=date(2026, 4, 21),
        fajr='04:18',
        sunrise='06:26',
        dhuhr='13:46',
        asr='17:39',
        maghrib='20:56',
        isha='22:46',
    )


# --- CALENDAR BUILDER: STRUCTURE ---


def test_build_creates_one_event_per_prayer(day1: PrayerDay):
    calendar = CalendarBuilder().build([day1])

    assert len(calendar.events) == 6


def test_build_creates_events_for_multiple_days(day1: PrayerDay, day2: PrayerDay):
    calendar = CalendarBuilder().build([day1, day2])

    assert len(calendar.events) == 12


def test_build_returns_empty_calendar_for_no_input():
    calendar = CalendarBuilder().build([])

    assert len(calendar.events) == 0


# --- CALENDAR BUILDER: UID PROPERTIES ---


def test_event_uids_are_unique_within_single_day(day1: PrayerDay):
    calendar = CalendarBuilder().build([day1])

    uids = [event.uid for event in calendar.events]

    assert len(uids) == len(set(uids))


def test_event_uids_are_unique_across_multiple_days(day1: PrayerDay, day2: PrayerDay):
    calendar = CalendarBuilder().build([day1, day2])

    uids = [event.uid for event in calendar.events]

    assert len(uids) == len(set(uids))


def test_uid_generation_is_stable_for_same_input(day1: PrayerDay):
    builder = CalendarBuilder()

    cal1 = builder.build([day1])
    cal2 = builder.build([day1])

    uids1 = sorted(event.uid for event in cal1.events)
    uids2 = sorted(event.uid for event in cal2.events)

    assert uids1 == uids2


# --- CALENDAR BUILDER: CONTENT ---


def test_event_names_are_correct(day1: PrayerDay):
    calendar = CalendarBuilder().build([day1])

    names = {event.name for event in calendar.events}

    assert names == {'Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'}


def test_event_datetime_is_parsed_correctly(day1: PrayerDay):
    calendar = CalendarBuilder().build([day1])

    fajr = next(e for e in calendar.events if e.name == 'Fajr')

    assert fajr.begin.hour == 4
    assert fajr.begin.minute == 20
    assert fajr.begin.date() == date(2026, 4, 20)


def test_event_times_are_increasing(day1: PrayerDay, day2: PrayerDay):
    calendar = CalendarBuilder().build([day2, day1])

    events = sorted(calendar.events, key=lambda e: e.begin)

    for earlier, later in zip(events, events[1:]):
        assert earlier.begin <= later.begin


# --- EDGE CASES ---


def test_invalid_time_format_raises():
    day = PrayerDay(
        date=date(2026, 4, 20),
        fajr='invalid',
        sunrise='06:28',
        dhuhr='13:46',
        asr='17:38',
        maghrib='20:54',
        isha='22:44',
    )

    with pytest.raises(ValueError):
        CalendarBuilder().build([day])
