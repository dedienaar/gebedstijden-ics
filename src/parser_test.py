from datetime import date
from pathlib import Path

from parser import HissaMonthParser


def _load_fixture(name: str) -> str:
    return (Path(__file__).parent / '__fixtures__' / name).read_text()


def test_parser_extracts_days():
    html = _load_fixture('hissa_month_apr.html')

    parser = HissaMonthParser()
    result = parser.parse(html)

    assert len(result) > 0

    first = result[0]

    assert first.date == date(2026, 4, 20)
    assert first.fajr == '4:20'
    assert first.isha == '22:44'


def test_year_rollover():
    html = _load_fixture('hissa_month_with_new_year.html')

    parser = HissaMonthParser()
    result = parser.parse(html)

    assert len(result) == 2

    assert result[0].date.year == 2026
    assert result[1].date.year == 2027
