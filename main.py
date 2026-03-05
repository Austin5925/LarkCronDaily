#!/usr/bin/env python3
"""
Lark Bitable Daily Row Copy Script

On each valid US business day, copies all rows from the previous valid
business day into today's date in a Lark (Feishu) Bitable table.

Designed to be run via cron. Exits silently on non-business days.
"""

import copy
import datetime
import logging
import sys

import config
from business_days import is_valid_business_day, previous_valid_business_day
from lark_api import (
    batch_create_records,
    date_to_timestamp_ms,
    get_tenant_access_token,
    search_records_by_date,
)

# ---------- Logging setup ----------


def setup_logging() -> None:
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if config.LOG_FILE:
        handlers.append(logging.FileHandler(config.LOG_FILE, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


# ---------- Main logic ----------


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    today = datetime.date.today()
    logger.info("Script started. Today is %s (%s).",
                today.isoformat(), today.strftime("%A"))

    # 1. Check if today is a valid business day
    if not is_valid_business_day(today):
        logger.info(
            "Today (%s) is not a valid business day. Exiting.", today.isoformat()
        )
        return

    # 2. Calculate the previous valid business day
    prev_day = previous_valid_business_day(today)
    logger.info("Previous valid business day: %s", prev_day.isoformat())

    # 3. Authenticate
    token = get_tenant_access_token()

    # 4. Search for records matching the previous business day
    records = search_records_by_date(token, prev_day)

    if not records:
        logger.warning(
            "No records found for %s. This may be expected after a long "
            "holiday. Nothing to copy.",
            prev_day.isoformat(),
        )
        return

    # 5. Build new records: deep-copy fields but replace date with today
    today_ts = date_to_timestamp_ms(today)
    new_records: list[dict] = []
    for rec in records:
        fields = copy.deepcopy(rec.get("fields", {}))
        fields[config.DATE_FIELD_NAME] = today_ts
        new_records.append({"fields": fields})

    logger.info(
        "Prepared %d new records (date: %s → %s).",
        len(new_records), prev_day.isoformat(), today.isoformat(),
    )

    # 6. Batch-write new records
    created = batch_create_records(token, new_records)

    logger.info(
        "Done. Copied %d rows from %s to %s.",
        created, prev_day.isoformat(), today.isoformat(),
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Unhandled exception")
        sys.exit(1)
