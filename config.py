"""
Configuration loaded from environment variables and .env file.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"ERROR: environment variable {name} is not set. "
              f"Check your .env file.", file=sys.stderr)
        sys.exit(1)
    return value


# Lark app credentials
LARK_APP_ID: str = _require_env("LARK_APP_ID")
LARK_APP_SECRET: str = _require_env("LARK_APP_SECRET")

# Bitable identifiers
BITABLE_APP_TOKEN: str = _require_env("BITABLE_APP_TOKEN")
BITABLE_TABLE_ID: str = _require_env("BITABLE_TABLE_ID")

# The field name that holds the date value (configurable)
DATE_FIELD_NAME: str = os.getenv("DATE_FIELD_NAME", "日期")

# Lark API base URL (feishu.cn for China, larksuite.com for international)
LARK_API_BASE: str = os.getenv("LARK_API_BASE", "https://open.feishu.cn")

# Log file path (optional)
LOG_FILE: str = os.getenv("LOG_FILE", "lark_daily_copy.log")
