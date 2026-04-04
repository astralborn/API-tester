"""Shared test data and helpers for the API-tester test suite."""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Sample preset data
# ---------------------------------------------------------------------------
SAMPLE_PRESETS: list[dict[str, Any]] = [
    {
        "name": "GetContacts Happy",
        "endpoint": "/api/intercom/GetContacts",
        "json_file": "get/normal_action/GetContacts_Normal_Action.json",
        "simple_format": False,
        "json_type": "normal",
    },
    {
        "name": "GetContacts Unhappy",
        "endpoint": "/api/intercom/GetContacts",
        "json_file": "get/unhappy/GetContacts_Unhappy.json",
        "simple_format": False,
        "json_type": "normal",
    },
    {
        "name": "GetSIPAccount",
        "endpoint": "/api/call/GetSIPAccount",
        "json_file": "get/normal_action/GetSIPAccount_Normal_Action.json",
        "simple_format": True,
        "json_type": "google",
    },
]

