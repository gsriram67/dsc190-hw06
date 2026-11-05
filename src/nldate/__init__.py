"""Natural-language date parser."""

import re
from collections.abc import Callable
from datetime import date, timedelta

_MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_NUMBER_WORDS: dict[str, int] = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

_ORDINAL_SUFFIX_RE = re.compile(r"(\d+)(st|nd|rd|th)\b", re.IGNORECASE)


def _strip_ordinal_suffix(s: str) -> str:
    return _ORDINAL_SUFFIX_RE.sub(r"\1", s)


def _parse_number_word(token: str) -> int | None:
    token = token.lower()
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _add_months(d: date, months: int) -> date:
    """Add (or subtract) months to a date, clamping the day if needed."""
    total = d.year * 12 + (d.month - 1) + months
    year = total // 12
    month = total % 12 + 1
    # Clamp day to last day of target month
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    day = min(d.day, last_day)
    return date(year, month, day)


def _add_years(d: date, years: int) -> date:
    return _add_months(d, years * 12)


def _find_absolute_date(s: str, today: date) -> date | None:
    """Try to find an absolute date in the string. Returns the date or None."""
    s_lower = s.lower()

    # ISO format: YYYY-MM-DD or YYYY/MM/DD
    m = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", s_lower)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            return None

    # US numeric format: MM/DD/YYYY or MM-DD-YYYY
    m = re.search(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b", s_lower)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            return None

    # Month name, day, year: "December 1st, 2025" / "Dec 1 2025" / "1 December 2025"
    s_clean = _strip_ordinal_suffix(s_lower)

    # Pattern: month_name day, year  or  month_name day year
    for month_name, month_num in _MONTHS.items():
        mn = rf"{month_name}\.?"
        # "december 1, 2025" or "december 1 2025" or "dec. 1, 2025"
        pattern = rf"\b{mn}\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*(\d{{4}})\b"
        m = re.search(pattern, s_clean)
        if m:
            day, year = int(m.group(1)), int(m.group(2))
            try:
                return date(year, month_num, day)
            except ValueError:
                return None
        # "december 2025" (no day -> use 1st)
        pattern = rf"\b{mn}\s+(\d{{4}})\b"
        m = re.search(pattern, s_clean)
        if m:
            year = int(m.group(1))
            try:
                return date(year, month_num, 1)
            except ValueError:
                return None
        # "1 december 2025" / "1st of december 2025" / "1 dec. 2025"
        pattern = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{mn}\s*,?\s*(\d{{4}})\b"
        m = re.search(pattern, s_clean)
        if m:
            day, year = int(m.group(1)), int(m.group(2))
            try:
                return date(year, month_num, day)
            except ValueError:
                return None

    # Month name + day, no year -> assume current year (or next year if past)
    for month_name, month_num in _MONTHS.items():
        mn = rf"{month_name}\.?"
        pattern = rf"\b{mn}\s+(\d{{1,2}})(?:st|nd|rd|th)?\b"
        m = re.search(pattern, s_clean)
        if m:
            day = int(m.group(1))
            try:
                result = date(today.year, month_num, day)
                if result < today:
                    result = date(today.year + 1, month_num, day)
                return result
            except ValueError:
                return None
        # day + month name, no year
        pattern = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{mn}\b"
        m = re.search(pattern, s_clean)
        if m:
            day = int(m.group(1))
            try:
                result = date(today.year, month_num, day)
                if result < today:
                    result = date(today.year + 1, month_num, day)
                return result
            except ValueError:
                return None

    return None


def _find_weekday(s: str, today: date) -> date | None:
    """Find 'next Tuesday', 'last Monday', 'this Friday', or bare 'Tuesday'."""
    s_lower = s.lower()
    for wd_name, wd_num in _WEEKDAYS.items():
        # "next tuesday"
        pattern = rf"\bnext\s+{wd_name}\b"
        if re.search(pattern, s_lower):
            days_ahead = (wd_num - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + timedelta(days=days_ahead)
        # "last monday"
        pattern = rf"\blast\s+{wd_name}\b"
        if re.search(pattern, s_lower):
            days_back = (today.weekday() - wd_num) % 7
            if days_back == 0:
                days_back = 7
            return today - timedelta(days=days_back)
        # "this friday"
        pattern = rf"\bthis\s+{wd_name}\b"
        if re.search(pattern, s_lower):
            days_ahead = (wd_num - today.weekday()) % 7
            return today + timedelta(days=days_ahead)
        # bare weekday name (e.g. "tuesday") -> next occurrence
        pattern = rf"\b{wd_name}\b"
        if re.search(pattern, s_lower):
            days_ahead = (wd_num - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + timedelta(days=days_ahead)
    return None


def _parse_relative(s: str, today: date) -> date | None:
    """Parse purely relative expressions like 'today', 'in 3 days', '2 weeks ago'."""
    s_lower = re.sub(r"\s+", " ", s.lower().strip())

    if s_lower in ("today",):
        return today
    if s_lower in ("tomorrow",):
        return today + timedelta(days=1)
    if s_lower in ("yesterday",):
        return today - timedelta(days=1)

    # "the day after tomorrow" / "day after tomorrow"
    if re.fullmatch(r"(the\s+)?day\s+after\s+tomorrow", s_lower):
        return today + timedelta(days=2)
    # "the day before yesterday" / "day before yesterday"
    if re.fullmatch(r"(the\s+)?day\s+before\s+yesterday", s_lower):
        return today - timedelta(days=2)
    # "the day before tomorrow"
    if re.fullmatch(r"(the\s+)?day\s+before\s+tomorrow", s_lower):
        return today
    # "the day after yesterday"
    if re.fullmatch(r"(the\s+)?day\s+after\s+yesterday", s_lower):
        return today

    # next/last/this week|month|year
    m = re.fullmatch(r"(next|last|this)\s+(week|month|year)", s_lower)
    if m:
        direction_word, unit = m.group(1), m.group(2)
        if direction_word == "next":
            n = 1
        elif direction_word == "last":
            n = -1
        else:  # this
            n = 0
        if unit == "week":
            return today + timedelta(weeks=n)
        if unit == "month":
            return _add_months(today, n)
        if unit == "year":
            return _add_years(today, n)

    # "in N days/weeks/months/years"
    m = re.match(r"^in\s+(.+)$", s_lower)
    if m:
        return _apply_offset(m.group(1), today, direction=1)

    # "N days/weeks/months/years from now"
    m = re.match(r"^(.+)\s+from\s+now$", s_lower)
    if m:
        return _apply_offset(m.group(1), today, direction=1)

    # "N days/weeks/months/years ago"
    m = re.match(r"^(.+)\s+ago$", s_lower)
    if m:
        return _apply_offset(m.group(1), today, direction=-1)

    # "N days/weeks/months/years from today/tomorrow/yesterday"
    m = re.match(r"^(.+)\s+from\s+(today|tomorrow|yesterday)$", s_lower)
    if m:
        base_str = m.group(2)
        if base_str == "today":
            base = today
        elif base_str == "tomorrow":
            base = today + timedelta(days=1)
        else:
            base = today - timedelta(days=1)
        return _apply_offset(m.group(1), base, direction=1)

    return None


def _apply_offset(expr: str, base: date, direction: int) -> date | None:
    """Apply a compound offset like '1 year and 2 months' or '3 days' to base."""
    result = base
    # Split on "and" or commas to handle compound offsets
    parts = re.split(r"\s+and\s+|\s*,\s*", expr.strip())
    for part in parts:
        part = part.strip()
        if not part:
            continue
        delta = _parse_single_offset(part, direction)
        if delta is None:
            return None
        result = delta(result)
    return result


def _parse_single_offset(part: str, direction: int) -> Callable[[date], date] | None:
    """Parse a single offset like '3 days' or '1 week'. Returns a function or None."""
    part = part.lower().strip()

    # Match: [number] [unit]
    m = re.match(r"^(.+?)\s+(day|days|week|weeks|month|months|year|years)$", part)
    if not m:
        return None

    num_str = m.group(1).strip()
    unit = m.group(2)
    n = _parse_number_word(num_str)
    if n is None:
        return None

    n *= direction

    if unit in ("day", "days"):
        return lambda d: d + timedelta(days=n)
    if unit in ("week", "weeks"):
        return lambda d: d + timedelta(weeks=n)
    if unit in ("month", "months"):
        return lambda d: _add_months(d, n)
    if unit in ("year", "years"):
        return lambda d: _add_years(d, n)
    return None


def _find_offset_around_anchor(s: str, today: date) -> date | None:
    """Handle patterns like 'N days before <date>' or 'N days after <date>'."""
    s_lower = s.lower()

    # "N <unit> before <rest>" or "N <unit> after <rest>"
    m = re.match(
        r"^(.+?)\s+(before|after|from)\s+(.+)$",
        s_lower,
    )
    if m:
        offset_expr = m.group(1).strip()
        direction_word = m.group(2)
        anchor_str = m.group(3).strip()

        # Parse the anchor (could be absolute date, weekday, or relative keyword)
        anchor = _find_absolute_date(anchor_str, today)
        if anchor is None:
            anchor = _find_weekday(anchor_str, today)
        if anchor is None:
            anchor = _parse_relative(anchor_str, today)
        if anchor is None:
            return None

        if direction_word == "before":
            direction = -1
        else:
            direction = 1

        return _apply_offset(offset_expr, anchor, direction)

    return None


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date string into a datetime.date.

    Args:
        s: Natural language date string (e.g. "5 days before December 1st, 2025").
        today: Reference date for relative expressions. Defaults to date.today().

    Returns:
        The parsed date.

    Raises:
        ValueError: If the string cannot be parsed as a date.
    """
    if today is None:
        today = date.today()

    if not s or not s.strip():
        raise ValueError(f"Cannot parse empty string as date: {s!r}")

    s = s.strip()

    # Try offset-around-anchor first (e.g. "5 days before December 1st, 2025")
    result = _find_offset_around_anchor(s, today)
    if result is not None:
        return result

    # Try absolute date
    result = _find_absolute_date(s, today)
    if result is not None:
        return result

    # Try weekday expressions
    result = _find_weekday(s, today)
    if result is not None:
        return result

    # Try purely relative expressions
    result = _parse_relative(s, today)
    if result is not None:
        return result

    raise ValueError(f"Cannot parse date string: {s!r}")
