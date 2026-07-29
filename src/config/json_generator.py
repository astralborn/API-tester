from __future__ import annotations

import json
import random
import secrets
import uuid
from pathlib import Path
from typing import Any

# ---------------- Configuration ----------------
# Paths are relative to this file's location (src/config/)
_HERE = Path(__file__).resolve().parent
JSON_FOLDER = _HERE / "json_configs"
PRESETS_FILE = _HERE / "presets.json"
ID_RPC = "helmut"
GOOGLE_CONTEXT = "test12345"
API_BASE_PATH = "/api"

# Test generation summary tracking
summary: dict[str, int] = {
    "normal": 0,
    "unhappy_no_data": 0,
    "unhappy_invalid": 0,
    "unhappy_wrong_type": 0,
    "unhappy_fuzz": 0,
}


# ---------------- Utility Functions ----------------
def generate_uuid_list(count: int = 1) -> list[str]:
    """Generate a list of UUID strings."""
    return [str(uuid.uuid4()) for _ in range(count)]


def save_json(path: Path, payload: Any) -> None:
    """Save payload to JSON file with proper directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def get_method_from_endpoint(endpoint: str) -> str:
    """Extract method name from endpoint URL."""
    return endpoint.split("/")[-1]


def get_section_from_endpoint(endpoint: str) -> str:
    """Determine section (get/set/remove) from endpoint."""
    if endpoint in GET_ENDPOINTS:
        return "get"
    elif endpoint in SET_ENDPOINTS:
        return "set"
    elif endpoint in REMOVE_ENDPOINTS:
        return "remove"
    else:
        return "unknown"


# ---------------- Data Generators ----------------
def generate_random_sip_account() -> dict[str, Any]:
    """Generate a random SIP account configuration."""
    return {
        "UserId": f"user{random.randint(1000, 9999)}",
        "Password": secrets.token_hex(8),
        "Registrar": f"192.168.0.{random.randint(1, 254)}",
        "PublicDomain": f"example{random.randint(1, 100)}.com",
    }


def generate_random_contact() -> dict[str, Any]:
    """Generate a random contact payload."""
    first_name = f"Tester {random.randint(1, 99):02d}"
    contact_id = str(uuid.uuid4())
    sip_address = f"192168{random.randint(1000, 9999)}"
    sip_account_id = f"sip_account_{random.randint(0, 9)}"
    return {
        "id": contact_id,
        "type": "Person",
        "firstName": first_name,
        "lastName": "",
        "callInformation": [{"type": "SIP", "address": sip_address, "accountid": sip_account_id}],
        "callForkingType": "sequential",
        "UIAttributes": [{"Name": "DisplayName", "Value": first_name}],
    }


# ---------------- API Endpoints ----------------
GET_ENDPOINTS = [
    "/api/intercom/GetContacts",
    "/api/call/GetSIPAccount",
    "/api/call/GetSIPAccounts",
    "/api/call/GetSIPAccountStatus",
    "/api/call/GetServiceCapabilities",
    "/api/call/GetSupportedSIPAccountAttributes",
    "/api/call/GetSupportedSIPConfigurationAttributes",
    "/api/call/GetSIPConfiguration",
    "/api/call/GetSupportedMediaEncryptionModes",
    "/api/call/GetDefaultAudioCodecs",
    "/api/call/GetSupportedAudioCodecs",
    "/api/call/GetAudioCodecs",
    "/api/call/GetCallStatus",
]

SET_ENDPOINTS = [
    "/api/call/SetSIPAccount",
    "/api/call/SetSIPAccounts",
    "/api/call/SetSIPConfiguration",
    "/api/call/SetAudioCodecs",
    "/api/call/Call",
    "/api/call/TerminateCall",
    "/api/intercom/SetContacts",
]

REMOVE_ENDPOINTS = [
    "/api/call/RemoveSIPAccount",
    "/api/call/RemoveSIPAccounts",
    "/api/intercom/RemoveContacts",
]

SPECIAL_PARAMS: dict[str, dict[str, Any]] = {
    "GetSIPAccountStatus": {"SIPAccountId": "sip_account_0"},
    "GetSIPAccount": {"SIPAccountId": "sip_account_0"},
    "GetCallStatus": {"CallId": "Out-18-18-SIP"},
}

REMOVE_PAYLOADS: dict[str, Any] = {
    "RemoveSIPAccount": {"SIPAccountId": "sip_account_0"},
    "RemoveSIPAccounts": {"SIPAccountId": ["sip_account_0", "sip_account_1"]},
    "RemoveContacts": {"ids": generate_uuid_list()},
}

SET_PAYLOADS: dict[str, Any] = {
    "SetSIPAccount": {"SIPAccount": generate_random_sip_account()},
    "SetSIPAccounts": {
        "SIPAccounts": {
            "SIPAccount": [generate_random_sip_account(), generate_random_sip_account()]
        }
    },
    "SetSIPConfiguration": {"SIPConfiguration": {"SIPEnabled": True}},
    "SetAudioCodecs": {"AudioCodec": [{"Name": "G.722", "SampleRate": 16000}]},
    "SetContacts": {"contacts": [generate_random_contact()]},
    "TerminateCall": {"CallId": "Out-18-18-SIP"},
    "Call": {"To": "sip:10.27.35.8:5060"},
}


# ---------------- Test Data Generators ----------------
def create_unhappy_payload(data: Any) -> Any:
    """Create payload with empty/null values for testing unhappy path."""
    if isinstance(data, dict):
        return {k: create_unhappy_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return []
    if isinstance(data, str):
        return ""
    if isinstance(data, (int, float)):
        return -1
    return None


def create_invalid_payload(data: Any) -> Any:
    """Create payload with invalid values for testing error handling."""
    if isinstance(data, dict):
        return {k: create_invalid_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return ["INVALID"]
    if isinstance(data, str):
        return "INVALID"
    if isinstance(data, (int, float)):
        return -999
    return "INVALID"


def create_wrong_type_payload(data: Any) -> Any:
    """Create payload with wrong data types for testing validation."""
    if isinstance(data, dict):
        return {k: create_wrong_type_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return "WRONG_TYPE"
    if isinstance(data, str):
        return 12345
    if isinstance(data, (int, float)):
        return "NOT_A_NUMBER"
    if isinstance(data, bool):
        return "true"
    return None


def create_fuzz_payload(data: Any) -> Any:
    """Create payload with fuzz testing values."""
    fuzz_strings = [
        "A" * 5000,
        "<script>alert(1)</script>",
        "' OR 1=1 --",
        "\x00\x01\x02",
        "漢字🚀",
    ]
    fuzz_numbers = [0, -1, 999999999999999999, float("inf"), float("-inf")]

    if isinstance(data, dict):
        return {k: create_fuzz_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [create_fuzz_payload(data[0])] if data else [None]
    if isinstance(data, str):
        return random.choice(fuzz_strings)
    if isinstance(data, (int, float)):
        return random.choice(fuzz_numbers)
    if isinstance(data, bool):
        return "TRUEEEEE"
    return None


# ---------------- Directory Setup ----------------
def setup_directory_structure() -> None:
    """Create the required directory structure for JSON configs."""
    sections = ["get", "set", "remove"]
    subfolders = ["normal_path", "normal_action", "normal_body", "google", "rpc"]

    for section in sections:
        for subfolder in subfolders:
            (JSON_FOLDER / section / subfolder).mkdir(parents=True, exist_ok=True)
        (JSON_FOLDER / section / "unhappy").mkdir(parents=True, exist_ok=True)


# ---------------- Preset Generation ----------------
def create_normal_presets(
    endpoints: list[str],
    payloads: dict[str, Any],
    section: str,
) -> list[dict[str, Any]]:
    """Create normal test presets for given endpoints."""
    presets = []
    formats = {
        "Normal_Path": "normal_path",
        "Normal_Action": "normal_action",
        "Normal_Body": "normal_body",
        "Google": "google",
        "RPC": "rpc",
    }

    for endpoint in endpoints:
        method = get_method_from_endpoint(endpoint)
        params = payloads.get(method, {})

        for format_name, subfolder in formats.items():
            file_name = f"{method}_{format_name}.json"
            file_path = JSON_FOLDER / section / subfolder / file_name
            # as_posix() gives forward slashes on all platforms
            json_file_relative = file_path.relative_to(JSON_FOLDER).as_posix()

            if format_name == "Normal_Body":
                payload = {method: params}
            elif format_name == "Google":
                payload = {
                    "apiVersion": "1.5",
                    "method": method,
                    "params": params,
                    "context": GOOGLE_CONTEXT,
                }
            elif format_name == "RPC":
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": ID_RPC,
                }
            else:
                payload = params

            save_json(file_path, payload)

            if format_name == "Normal_Action":
                endpoint_url = f"{endpoint}?action={method}"
            elif format_name == "Normal_Path":
                endpoint_url = endpoint
            else:
                endpoint_url = "/".join(endpoint.split("/")[:-1])

            summary["normal"] += 1

            presets.append(
                {
                    "name": f"{method}_{format_name}",
                    "endpoint": endpoint_url,
                    "json_file": json_file_relative,
                    "simple_format": False,
                    "json_type": "normal"
                    if format_name.startswith("Normal")
                    else format_name.lower(),
                }
            )

    return presets


def create_unhappy_tests(
    endpoints: list[str],
    payloads: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create unhappy path test presets for error testing."""
    unhappy_presets = []
    test_types = [
        ("no_data", create_unhappy_payload, "unhappy_no_data"),
        ("invalid_data", create_invalid_payload, "unhappy_invalid"),
        ("wrong_type", create_wrong_type_payload, "unhappy_wrong_type"),
        ("fuzz", create_fuzz_payload, "unhappy_fuzz"),
    ]

    for endpoint in endpoints:
        method = get_method_from_endpoint(endpoint)
        params = payloads.get(method) or SPECIAL_PARAMS.get(method)
        if not params:
            continue

        section = get_section_from_endpoint(endpoint)
        folder = JSON_FOLDER / section / "unhappy"

        for test_suffix, payload_generator, summary_key in test_types:
            test_payload = payload_generator(params)
            file_name = f"{method}_unhappy_{test_suffix}.json"
            file_path = folder / file_name
            save_json(file_path, test_payload)

            unhappy_presets.append(
                {
                    "name": f"{method}_unhappy_{test_suffix}",
                    "endpoint": endpoint,
                    "json_file": file_path.relative_to(JSON_FOLDER).as_posix(),
                    "simple_format": False,
                    "json_type": "normal",
                }
            )

            summary[summary_key] += 1

    return unhappy_presets


# ---------------- Main Execution ----------------
def main() -> None:
    """Main function to generate all test presets."""
    print("🚀 Starting API test preset generation...")

    setup_directory_structure()
    print("📁 Directory structure created")

    all_presets: list[dict[str, Any]] = []

    all_presets += create_normal_presets(GET_ENDPOINTS, SPECIAL_PARAMS, "get")
    all_presets += create_normal_presets(SET_ENDPOINTS, SET_PAYLOADS, "set")
    all_presets += create_normal_presets(REMOVE_ENDPOINTS, REMOVE_PAYLOADS, "remove")
    print("✅ Normal presets generated")

    all_payloads = {**SET_PAYLOADS, **SPECIAL_PARAMS, **REMOVE_PAYLOADS}
    all_endpoints = GET_ENDPOINTS + SET_ENDPOINTS + REMOVE_ENDPOINTS
    all_presets += create_unhappy_tests(all_endpoints, all_payloads)
    print("🔧 Unhappy test presets generated")

    with PRESETS_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_presets, f, indent=2)
    print(f"💾 Presets saved to {PRESETS_FILE}")

    total_tests = sum(summary.values())
    print("\n📊 TEST GENERATION SUMMARY")
    print(f"   Normal tests:        {summary['normal']}")
    print(f"   Unhappy no data:     {summary['unhappy_no_data']}")
    print(f"   Unhappy invalid:     {summary['unhappy_invalid']}")
    print(f"   Unhappy wrong type:  {summary['unhappy_wrong_type']}")
    print(f"   Unhappy fuzz:        {summary['unhappy_fuzz']}")
    print(f"   TOTAL TESTS:         {total_tests}")
    print("\n✅ All presets generated successfully!")


if __name__ == "__main__":
    main()
