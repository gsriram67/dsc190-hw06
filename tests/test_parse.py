"""Tests for nldate.parse()."""

from datetime import date

import pytest

from nldate import parse

# Reference date: Wednesday, November 5, 2025
TODAY = date(2025, 11, 5)


class TestAbsoluteDates:
    def test_iso_format(self) -> None:
        assert parse("2025-12-01", today=TODAY) == date(2025, 12, 1)

    def test_iso_format_slash(self) -> None:
        assert parse("2025/12/04", today=TODAY) == date(2025, 12, 4)

    def test_us_numeric_format_slash(self) -> None:
        assert parse("12/01/2025", today=TODAY) == date(2025, 12, 1)

    def test_us_numeric_format_dash(self) -> None:
        assert parse("12-01-2025", today=TODAY) == date(2025, 12, 1)

    def test_month_name_day_year(self) -> None:
        assert parse("December 1st, 2025", today=TODAY) == date(2025, 12, 1)

    def test_month_name_day_year_no_ordinal(self) -> None:
        assert parse("December 1, 2025", today=TODAY) == date(2025, 12, 1)

    def test_abbreviated_month(self) -> None:
        assert parse("Dec 1 2025", today=TODAY) == date(2025, 12, 1)

    def test_abbreviated_month_with_period(self) -> None:
        assert parse("Dec. 1, 2025", today=TODAY) == date(2025, 12, 1)

    def test_day_month_year(self) -> None:
        assert parse("1 December 2025", today=TODAY) == date(2025, 12, 1)

    def test_day_of_month_year(self) -> None:
        assert parse("1st of December 2025", today=TODAY) == date(2025, 12, 1)

    def test_month_day_no_year_future(self) -> None:
        # December 25 is after Nov 5, so same year
        assert parse("December 25", today=TODAY) == date(2025, 12, 25)

    def test_month_day_no_year_past(self) -> None:
        # October 10 is before Nov 5, so next year
        assert parse("October 10", today=TODAY) == date(2026, 10, 10)


class TestRelativeDates:
    def test_today(self) -> None:
        assert parse("today", today=TODAY) == TODAY

    def test_tomorrow(self) -> None:
        assert parse("tomorrow", today=TODAY) == date(2025, 11, 6)

    def test_yesterday(self) -> None:
        assert parse("yesterday", today=TODAY) == date(2025, 11, 4)

    def test_in_n_days(self) -> None:
        assert parse("in 3 days", today=TODAY) == date(2025, 11, 8)

    def test_n_days_from_now(self) -> None:
        assert parse("5 days from now", today=TODAY) == date(2025, 11, 10)

    def test_n_days_ago(self) -> None:
        assert parse("2 days ago", today=TODAY) == date(2025, 11, 3)

    def test_in_n_weeks(self) -> None:
        assert parse("in 2 weeks", today=TODAY) == date(2025, 11, 19)

    def test_n_weeks_ago(self) -> None:
        assert parse("1 week ago", today=TODAY) == date(2025, 10, 29)

    def test_in_n_months(self) -> None:
        assert parse("in 2 months", today=TODAY) == date(2026, 1, 5)

    def test_n_months_ago(self) -> None:
        assert parse("3 months ago", today=TODAY) == date(2025, 8, 5)

    def test_in_n_years(self) -> None:
        assert parse("in 1 year", today=TODAY) == date(2026, 11, 5)

    def test_n_years_ago(self) -> None:
        assert parse("2 years ago", today=TODAY) == date(2023, 11, 5)

    def test_word_number_days(self) -> None:
        assert parse("in five days", today=TODAY) == date(2025, 11, 10)

    def test_two_weeks_from_tomorrow(self) -> None:
        assert parse("two weeks from tomorrow", today=TODAY) == date(2025, 11, 20)

    def test_next_week(self) -> None:
        assert parse("next week", today=TODAY) == date(2025, 11, 12)

    def test_last_week(self) -> None:
        assert parse("last week", today=TODAY) == date(2025, 10, 29)

    def test_this_week(self) -> None:
        assert parse("this week", today=TODAY) == TODAY

    def test_next_month(self) -> None:
        assert parse("next month", today=TODAY) == date(2025, 12, 5)

    def test_last_month(self) -> None:
        assert parse("last month", today=TODAY) == date(2025, 10, 5)

    def test_next_year(self) -> None:
        assert parse("next year", today=TODAY) == date(2026, 11, 5)

    def test_last_year(self) -> None:
        assert parse("last year", today=TODAY) == date(2024, 11, 5)

    def test_day_after_tomorrow(self) -> None:
        assert parse("the day after tomorrow", today=TODAY) == date(2025, 11, 7)

    def test_day_before_yesterday(self) -> None:
        assert parse("day before yesterday", today=TODAY) == date(2025, 11, 3)

    def test_in_a_week(self) -> None:
        assert parse("in a week", today=TODAY) == date(2025, 11, 12)

    def test_a_month_ago(self) -> None:
        assert parse("a month ago", today=TODAY) == date(2025, 10, 5)


class TestWeekdays:
    def test_next_tuesday(self) -> None:
        # TODAY is Wednesday Nov 5; next Tuesday is Nov 11
        assert parse("next Tuesday", today=TODAY) == date(2025, 11, 11)

    def test_last_monday(self) -> None:
        # Last Monday before Wed Nov 5 is Nov 3
        assert parse("last Monday", today=TODAY) == date(2025, 11, 3)

    def test_this_friday(self) -> None:
        # This Friday from Wed Nov 5 is Nov 7
        assert parse("this Friday", today=TODAY) == date(2025, 11, 7)

    def test_bare_weekday(self) -> None:
        # Bare "Saturday" -> next Saturday from Wed Nov 5 is Nov 8
        assert parse("Saturday", today=TODAY) == date(2025, 11, 8)

    def test_next_wednesday_same_day(self) -> None:
        # TODAY is Wednesday; "next Wednesday" should be 7 days later
        assert parse("next Wednesday", today=TODAY) == date(2025, 11, 12)


class TestOffsetAroundAnchor:
    def test_days_before_absolute(self) -> None:
        assert parse("5 days before December 1st, 2025", today=TODAY) == date(
            2025, 11, 26
        )

    def test_days_after_absolute(self) -> None:
        assert parse("3 days after December 1, 2025", today=TODAY) == date(2025, 12, 4)

    def test_weeks_before_absolute(self) -> None:
        assert parse("2 weeks before 2025-12-01", today=TODAY) == date(2025, 11, 17)

    def test_days_before_tomorrow(self) -> None:
        assert parse("2 days before tomorrow", today=TODAY) == date(2025, 11, 4)

    def test_compound_offset_after_yesterday(self) -> None:
        # yesterday = Nov 4; +1 year +2 months = Jan 4, 2027
        assert parse("1 year and 2 months after yesterday", today=TODAY) == date(
            2027, 1, 4
        )

    def test_days_from_absolute(self) -> None:
        assert parse("10 days from January 15, 2026", today=TODAY) == date(2026, 1, 25)


class TestErrors:
    def test_empty_string(self) -> None:
        with pytest.raises(ValueError):
            parse("", today=TODAY)

    def test_whitespace_only(self) -> None:
        with pytest.raises(ValueError):
            parse("   ", today=TODAY)

    def test_garbage(self) -> None:
        with pytest.raises(ValueError):
            parse("hello world", today=TODAY)

    def test_invalid_date(self) -> None:
        with pytest.raises(ValueError):
            parse("not a date at all", today=TODAY)


class TestDefaultToday:
    def test_default_today_used(self) -> None:
        result = parse("today")
        assert result == date.today()
