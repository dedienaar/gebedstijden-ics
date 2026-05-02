from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from calendar_builder import CalendarBuilder, IcsWriter, generate_uid
from models import PrayerDay


# --- helper ---
def build_calendar(days: list[PrayerDay]):
    builder = CalendarBuilder()
    builder.add_events(days)
    return builder.build()


# --- UID GENERATOR ---


@pytest.mark.parametrize(
    'name',
    ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'],
)
def test_uid_generator_is_deterministic_per_input(name: str):
    uid1 = generate_uid(date(2026, 4, 20), name)
    uid2 = generate_uid(date(2026, 4, 20), name)
    assert uid1 == uid2


@pytest.mark.parametrize(
    'date1, date2',
    [
        (date(2026, 4, 20), date(2026, 4, 21)),
        (date(2026, 1, 1), date(2026, 12, 31)),
    ],
)
def test_uid_generator_varies_with_date(date1: date, date2: date):
    uid1 = generate_uid(date1, 'Fajr')
    uid2 = generate_uid(date2, 'Fajr')
    assert uid1 != uid2


@pytest.mark.parametrize(
    'name1, name2',
    [
        ('Fajr', 'Sunrise'),
        ('Dhuhr', 'Asr'),
    ],
)
def test_uid_generator_varies_with_event_name(name1: str, name2: str):
    uid1 = generate_uid(date(2026, 4, 20), name1)
    uid2 = generate_uid(date(2026, 4, 20), name2)
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


@pytest.fixture
def expected_event_names():
    return {
        '🌃 Fajr',
        '🌅 Sunrise',
        '🏙️ Dhuhr',
        '🌆 Asr',
        '🌄 Maghrib',
        '🌌 Isha',
    }


# --- CALENDAR BUILDER ---


def test_build_creates_one_event_per_prayer(day1: PrayerDay):
    result = build_calendar([day1])
    assert len(result.events) == 6


def test_build_creates_events_for_multiple_days(day1: PrayerDay, day2: PrayerDay):
    result = build_calendar([day1, day2])
    assert len(result.events) == 12


def test_build_returns_empty_calendar_for_no_input():
    result = build_calendar([])
    assert len(result.events) == 0


def test_add_metadata_prevents_duplicates():
    builder = CalendarBuilder()
    builder.add_metadata('X-CUSTOM', 'value1')
    builder.add_metadata('X-CUSTOM', 'value2')
    result = builder.build()

    custom_properties = [
        item for item in result.calendar.property_items() if item[0] == 'X-CUSTOM'
    ]
    assert len(custom_properties) == 1
    assert custom_properties[0][1] == 'value2'


# --- UID PROPERTIES ---


def test_event_uids_are_unique_within_single_day(day1: PrayerDay):
    result = build_calendar([day1])
    uids = [event.uid for event in result.events]
    assert len(uids) == len(set(uids))


def test_event_uids_are_unique_across_multiple_days(day1: PrayerDay, day2: PrayerDay):
    result = build_calendar([day1, day2])
    uids = [event.uid for event in result.events]
    assert len(uids) == len(set(uids))


def test_uid_generation_is_stable_for_same_input(day1: PrayerDay):
    cal1 = build_calendar([day1])
    cal2 = build_calendar([day1])

    uids1 = sorted(event.uid for event in cal1.events)
    uids2 = sorted(event.uid for event in cal2.events)

    assert uids1 == uids2


# --- CONTENT ---


def test_event_names_are_correct(day1: PrayerDay, expected_event_names):
    result = build_calendar([day1])
    names = {event.name for event in result.events}

    assert names == expected_event_names


def test_event_datetime_is_parsed_correctly(day1: PrayerDay):
    result = build_calendar([day1])

    fajr = next(e for e in result.events if e.name == '🌃 Fajr')

    assert fajr.begin.hour == 4
    assert fajr.begin.minute == 20
    assert fajr.begin.date() == date(2026, 4, 20)


def test_event_times_are_increasing(day1: PrayerDay, day2: PrayerDay):
    result = build_calendar([day2, day1])
    events = sorted(result.events, key=lambda e: e.begin)

    for earlier, later in zip(events, events[1:]):
        assert earlier.begin <= later.begin


# --- EDGE CASES ---


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
        build_calendar([day])


def test_writer_persists_ics(day1: PrayerDay, tmp_path: Path):
    result = build_calendar([day1])
    output = tmp_path / 'prayer_times.ics'

    written_path = IcsWriter(output).write(result.calendar)

    assert written_path.exists()

    content = written_path.read_text(encoding='utf-8')

    assert 'BEGIN:VCALENDAR' in content
    assert 'END:VCALENDAR' in content
    assert 'VERSION:2.0' in content

    assert content.count('BEGIN:VEVENT') == 6
    assert 'SUMMARY:🌃 Fajr' in content
    assert 'SUMMARY:🌅 Sunrise' in content
    assert 'SUMMARY:🏙️ Dhuhr' in content
    assert 'SUMMARY:🌆 Asr' in content
    assert 'SUMMARY:🌄 Maghrib' in content
    assert 'SUMMARY:🌌 Isha' in content


def test_ics_datetime_format_is_valid(day1: PrayerDay, tmp_path: Path):
    import re

    result = build_calendar([day1])
    output = tmp_path / 'prayer_times.ics'

    content = IcsWriter(output).write(result.calendar).read_text(encoding='utf-8')

    for field in ('DTSTART', 'DTEND'):
        matches = re.findall(rf'{field};TZID=[^:]+:\d{{8}}T\d{{6}}', content)
        assert len(matches) == 6
