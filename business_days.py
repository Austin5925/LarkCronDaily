"""
US Federal Reserve Bank Holidays & valid business day calculations.

Uses the `holidays` library for accurate Federal Reserve holiday schedules,
including Saturday→Friday and Sunday→Monday observed-date rules.
"""

import datetime
from functools import lru_cache

import holidays


@lru_cache(maxsize=8)
def _us_bank_holidays(year: int) -> holidays.HolidayBase:
    """Return a holidays object for US Federal Reserve bank holidays."""
    # holidays.FederalReserve covers all 11 Federal Reserve holidays
    # with proper observed-date rules (Sat→Fri, Sun→Mon).
    return holidays.country_holidays("US", categories="government", years=year)


def is_us_bank_holiday(date: datetime.date) -> bool:
    """Check if a date is a US Federal Reserve bank holiday (observed)."""
    h = _us_bank_holidays(date.year)
    return date in h


def is_valid_business_day(date: datetime.date) -> bool:
    """
    A valid business day is Monday–Friday AND not a US bank holiday.
    """
    if date.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return not is_us_bank_holiday(date)


def previous_valid_business_day(date: datetime.date) -> datetime.date:
    """
    Return the most recent valid business day strictly before `date`.
    Walks backwards day-by-day until a valid business day is found.
    """
    d = date - datetime.timedelta(days=1)
    while not is_valid_business_day(d):
        d -= datetime.timedelta(days=1)
    return d
