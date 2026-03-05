"""
Lark (Feishu) Bitable API wrapper.

Handles authentication, record searching, and batch record creation
with retry logic and pagination.
"""

import datetime
import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

# ---------- Constants ----------

_TOKEN_URL = f"{config.LARK_API_BASE}/open-apis/auth/v3/tenant_access_token/internal"
_SEARCH_URL = (
    f"{config.LARK_API_BASE}/open-apis/bitable/v1/apps/"
    f"{config.BITABLE_APP_TOKEN}/tables/{config.BITABLE_TABLE_ID}/records/search"
)
_BATCH_CREATE_URL = (
    f"{config.LARK_API_BASE}/open-apis/bitable/v1/apps/"
    f"{config.BITABLE_APP_TOKEN}/tables/{config.BITABLE_TABLE_ID}/records/batch_create"
)

MAX_RETRIES = 3
BATCH_SIZE = 500  # Lark API limit per batch_create call


# ---------- Helpers ----------


def _retry_request(method: str, url: str, **kwargs) -> dict:
    """
    Make an HTTP request with exponential-backoff retry (up to MAX_RETRIES).
    Returns the parsed JSON response body.
    Raises on non-200 status or Lark API error code != 0.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            data = resp.json()
            code = data.get("code", -1)
            if code == 0:
                return data
            # Lark API returned an error
            msg = data.get("msg", "unknown error")
            logger.warning(
                "Lark API error (attempt %d/%d): code=%s msg=%s",
                attempt, MAX_RETRIES, code, msg,
            )
        except requests.RequestException as exc:
            logger.warning(
                "HTTP error (attempt %d/%d): %s", attempt, MAX_RETRIES, exc
            )
            data = None

        if attempt < MAX_RETRIES:
            wait = 2 ** attempt  # 2, 4 seconds
            logger.info("Retrying in %d seconds ...", wait)
            time.sleep(wait)

    raise RuntimeError(
        f"Lark API request failed after {MAX_RETRIES} attempts: {url}"
    )


# ---------- Authentication ----------


def get_tenant_access_token() -> str:
    """Obtain a fresh tenant_access_token (valid for ~2 hours)."""
    payload = {
        "app_id": config.LARK_APP_ID,
        "app_secret": config.LARK_APP_SECRET,
    }
    data = _retry_request("POST", _TOKEN_URL, json=payload)
    token = data.get("tenant_access_token", "")
    if not token:
        raise RuntimeError("Failed to obtain tenant_access_token")
    logger.info("Obtained tenant_access_token successfully.")
    return token


def _auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------- Date helpers ----------


def date_to_timestamp_ms(d: datetime.date) -> int:
    """Convert a date to a millisecond Unix timestamp (midnight UTC)."""
    dt = datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
    return int(dt.timestamp() * 1000)


# ---------- Search records ----------


def search_records_by_date(
    token: str, date: datetime.date
) -> list[dict]:
    """
    Search the Bitable table for all records whose date field equals `date`.

    The Lark search API uses a filter with conjunction/conditions structure.
    Date fields are stored as millisecond timestamps — we match against the
    timestamp of midnight UTC on the target date.

    Returns a list of record dicts, each containing 'fields' and 'record_id'.
    Handles pagination automatically.
    """
    ts = date_to_timestamp_ms(date)
    headers = _auth_headers(token)

    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": config.DATE_FIELD_NAME,
                    "operator": "is",
                    "value": [str(ts)],
                }
            ],
        },
        "page_size": 500,
    }

    all_records: list[dict] = []
    page_token = ""

    while True:
        url = _SEARCH_URL
        if page_token:
            url = f"{_SEARCH_URL}?page_token={page_token}"

        data = _retry_request("POST", url, headers=headers, json=payload)
        items = data.get("data", {}).get("items", [])
        all_records.extend(items or [])

        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token", "")
        if not has_more:
            break

    logger.info(
        "Found %d records for date %s (ts=%d).",
        len(all_records), date.isoformat(), ts,
    )
    return all_records


# ---------- Create records ----------


def batch_create_records(token: str, records: list[dict]) -> int:
    """
    Batch-create records in the Bitable table.
    Each record should be a dict like {"fields": {...}}.
    Handles splitting into chunks of BATCH_SIZE (500).
    Returns the total number of records created.
    """
    headers = _auth_headers(token)
    total_created = 0

    for i in range(0, len(records), BATCH_SIZE):
        chunk = records[i : i + BATCH_SIZE]
        payload = {"records": chunk}
        data = _retry_request(
            "POST", _BATCH_CREATE_URL, headers=headers, json=payload
        )
        created = len(data.get("data", {}).get("records", []))
        total_created += created
        logger.info(
            "Batch %d: created %d records.", i // BATCH_SIZE + 1, created
        )

    return total_created
