"""Tests for config/json_generator.py — payload generators and preset creation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_summary():
    """Reset the module-level summary counters before each test."""
    from config.json_generator import summary

    original = summary.copy()
    summary.update({k: 0 for k in summary})
    yield
    summary.update(original)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

class TestGenerateUuidList:
    def test_returns_list_of_strings(self):
        from config.json_generator import generate_uuid_list

        result = generate_uuid_list(3)
        assert len(result) == 3
        assert all(isinstance(s, str) for s in result)

    def test_default_count_is_one(self):
        from config.json_generator import generate_uuid_list

        assert len(generate_uuid_list()) == 1

    def test_uuids_are_unique(self):
        from config.json_generator import generate_uuid_list

        result = generate_uuid_list(10)
        assert len(set(result)) == 10


class TestSaveJson:
    def test_creates_file_with_json_content(self, tmp_path):
        from config.json_generator import save_json

        path = tmp_path / "sub" / "test.json"
        save_json(path, {"key": "value"})
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8")) == {"key": "value"}

    def test_creates_parent_directories(self, tmp_path):
        from config.json_generator import save_json

        path = tmp_path / "a" / "b" / "c" / "file.json"
        save_json(path, [1, 2, 3])
        assert path.exists()


class TestGetMethodFromEndpoint:
    def test_extracts_last_path_segment(self):
        from config.json_generator import get_method_from_endpoint

        assert get_method_from_endpoint("/api/call/GetSIPAccount") == "GetSIPAccount"
        assert get_method_from_endpoint("/api/intercom/GetContacts") == "GetContacts"

    def test_single_segment(self):
        from config.json_generator import get_method_from_endpoint

        assert get_method_from_endpoint("Method") == "Method"


class TestGetSectionFromEndpoint:
    def test_get_endpoints(self):
        from config.json_generator import get_section_from_endpoint

        assert get_section_from_endpoint("/api/intercom/GetContacts") == "get"

    def test_set_endpoints(self):
        from config.json_generator import get_section_from_endpoint

        assert get_section_from_endpoint("/api/call/SetSIPAccount") == "set"

    def test_remove_endpoints(self):
        from config.json_generator import get_section_from_endpoint

        assert get_section_from_endpoint("/api/call/RemoveSIPAccount") == "remove"

    def test_unknown_endpoint(self):
        from config.json_generator import get_section_from_endpoint

        assert get_section_from_endpoint("/api/unknown/Foo") == "unknown"


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

class TestGenerateRandomSipAccount:
    def test_returns_dict_with_expected_keys(self):
        from config.json_generator import generate_random_sip_account

        result = generate_random_sip_account()
        assert set(result.keys()) == {"UserId", "Password", "Registrar", "PublicDomain"}

    def test_values_are_strings(self):
        from config.json_generator import generate_random_sip_account

        result = generate_random_sip_account()
        assert all(isinstance(v, str) for v in result.values())


class TestGenerateRandomContact:
    def test_returns_dict_with_expected_keys(self):
        from config.json_generator import generate_random_contact

        result = generate_random_contact()
        assert "id" in result
        assert "type" in result
        assert "firstName" in result
        assert "callInformation" in result
        assert result["type"] == "Person"

    def test_call_information_is_list(self):
        from config.json_generator import generate_random_contact

        result = generate_random_contact()
        assert isinstance(result["callInformation"], list)
        assert len(result["callInformation"]) == 1


# ---------------------------------------------------------------------------
# Payload transformation functions
# ---------------------------------------------------------------------------

class TestCreateUnhappyPayload:
    def test_dict_values_emptied(self):
        from config.json_generator import create_unhappy_payload

        result = create_unhappy_payload({"name": "Alice", "age": 30})
        assert result == {"name": "", "age": -1}

    def test_list_becomes_empty(self):
        from config.json_generator import create_unhappy_payload

        assert create_unhappy_payload([1, 2, 3]) == []

    def test_string_becomes_empty(self):
        from config.json_generator import create_unhappy_payload

        assert create_unhappy_payload("hello") == ""

    def test_number_becomes_negative_one(self):
        from config.json_generator import create_unhappy_payload

        assert create_unhappy_payload(42) == -1
        assert create_unhappy_payload(3.14) == -1

    def test_none_stays_none(self):
        from config.json_generator import create_unhappy_payload

        assert create_unhappy_payload(None) is None

    def test_nested_dict(self):
        from config.json_generator import create_unhappy_payload

        result = create_unhappy_payload({"a": {"b": "val", "c": [1]}})
        assert result == {"a": {"b": "", "c": []}}


class TestCreateInvalidPayload:
    def test_dict_values_become_invalid(self):
        from config.json_generator import create_invalid_payload

        result = create_invalid_payload({"name": "Bob"})
        assert result == {"name": "INVALID"}

    def test_list_becomes_invalid_list(self):
        from config.json_generator import create_invalid_payload

        assert create_invalid_payload([1, 2]) == ["INVALID"]

    def test_number_becomes_negative_999(self):
        from config.json_generator import create_invalid_payload

        assert create_invalid_payload(100) == -999

    def test_none_becomes_invalid_string(self):
        from config.json_generator import create_invalid_payload

        assert create_invalid_payload(None) == "INVALID"


class TestCreateWrongTypePayload:
    def test_string_becomes_int(self):
        from config.json_generator import create_wrong_type_payload

        assert create_wrong_type_payload("hello") == 12345

    def test_int_becomes_string(self):
        from config.json_generator import create_wrong_type_payload

        assert create_wrong_type_payload(42) == "NOT_A_NUMBER"

    def test_list_becomes_string(self):
        from config.json_generator import create_wrong_type_payload

        assert create_wrong_type_payload([1, 2]) == "WRONG_TYPE"

    def test_nested_dict(self):
        from config.json_generator import create_wrong_type_payload

        result = create_wrong_type_payload({"items": [1], "name": "x"})
        assert result == {"items": "WRONG_TYPE", "name": 12345}


class TestCreateFuzzPayload:
    def test_string_becomes_fuzz_string(self):
        from config.json_generator import create_fuzz_payload

        fuzz_strings = [
            "A" * 5000, "<script>alert(1)</script>",
            "' OR 1=1 --", "\x00\x01\x02", "漢字🚀",
        ]
        result = create_fuzz_payload("test")
        assert result in fuzz_strings

    def test_number_becomes_fuzz_number(self):
        from config.json_generator import create_fuzz_payload

        fuzz_numbers = [0, -1, 999999999999999999, float("inf"), float("-inf")]
        result = create_fuzz_payload(42)
        assert result in fuzz_numbers

    def test_bool_hits_int_branch_due_to_subclass(self):
        """Note: bool is a subclass of int in Python, so True/False hit the int branch."""
        from config.json_generator import create_fuzz_payload

        fuzz_numbers = [0, -1, 999999999999999999, float("inf"), float("-inf")]
        # True/False are ints, so they get fuzz numbers instead of "TRUEEEEE"
        assert create_fuzz_payload(True) in fuzz_numbers
        assert create_fuzz_payload(False) in fuzz_numbers

    def test_empty_list_returns_none_element(self):
        from config.json_generator import create_fuzz_payload

        assert create_fuzz_payload([]) == [None]

    def test_non_empty_list_fuzzes_first_element(self):
        from config.json_generator import create_fuzz_payload

        result = create_fuzz_payload(["hello"])
        assert isinstance(result, list)
        assert len(result) == 1

    def test_dict_recurses(self):
        from config.json_generator import create_fuzz_payload

        result = create_fuzz_payload({"key": "value"})
        assert isinstance(result, dict)
        assert "key" in result
        assert result["key"] != "value"


# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------

class TestSetupDirectoryStructure:
    def test_creates_expected_directories(self, tmp_path):
        from config.json_generator import setup_directory_structure

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            setup_directory_structure()

        sections = ["get", "set", "remove"]
        subfolders = ["normal_path", "normal_action", "normal_body", "google", "rpc", "unhappy"]

        for section in sections:
            for subfolder in subfolders:
                assert (tmp_path / section / subfolder).is_dir()


# ---------------------------------------------------------------------------
# Preset generation
# ---------------------------------------------------------------------------

class TestCreateNormalPresets:
    def test_generates_five_formats_per_endpoint(self, tmp_path):
        from config.json_generator import create_normal_presets

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            presets = create_normal_presets(
                ["/api/call/GetSIPAccount"],
                {"GetSIPAccount": {"SIPAccountId": "sip_account_0"}},
                "get",
            )

        assert len(presets) == 5
        names = [p["name"] for p in presets]
        assert "GetSIPAccount_Normal_Path" in names
        assert "GetSIPAccount_Normal_Action" in names
        assert "GetSIPAccount_Normal_Body" in names
        assert "GetSIPAccount_Google" in names
        assert "GetSIPAccount_RPC" in names

    def test_creates_json_files_on_disk(self, tmp_path):
        from config.json_generator import create_normal_presets

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            create_normal_presets(
                ["/api/call/GetSIPAccount"],
                {"GetSIPAccount": {"id": "test"}},
                "get",
            )

        json_files = list(tmp_path.rglob("*.json"))
        assert len(json_files) == 5

    def test_google_format_has_correct_structure(self, tmp_path):
        from config.json_generator import create_normal_presets

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            presets = create_normal_presets(
                ["/api/call/GetSIPAccount"],
                {"GetSIPAccount": {"SIPAccountId": "test"}},
                "get",
            )

        google_preset = next(p for p in presets if "Google" in p["name"])
        json_path = tmp_path / google_preset["json_file"]
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["apiVersion"] == "1.5"
        assert payload["method"] == "GetSIPAccount"
        assert "params" in payload
        assert "context" in payload

    def test_rpc_format_has_correct_structure(self, tmp_path):
        from config.json_generator import create_normal_presets

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            presets = create_normal_presets(
                ["/api/call/GetSIPAccount"],
                {"GetSIPAccount": {"SIPAccountId": "test"}},
                "get",
            )

        rpc_preset = next(p for p in presets if "RPC" in p["name"])
        json_path = tmp_path / rpc_preset["json_file"]
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["jsonrpc"] == "2.0"
        assert payload["method"] == "GetSIPAccount"
        assert "id" in payload

    def test_increments_summary_counter(self, tmp_path):
        from config.json_generator import create_normal_presets, summary

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            create_normal_presets(
                ["/api/call/GetSIPAccount"],
                {"GetSIPAccount": {}},
                "get",
            )

        assert summary["normal"] == 5


class TestCreateUnhappyTests:
    def test_generates_four_test_types(self, tmp_path):
        from config.json_generator import create_unhappy_tests

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            presets = create_unhappy_tests(
                ["/api/call/SetSIPAccount"],
                {"SetSIPAccount": {"SIPAccount": {"UserId": "test"}}},
            )

        assert len(presets) == 4
        names = [p["name"] for p in presets]
        assert "SetSIPAccount_unhappy_no_data" in names
        assert "SetSIPAccount_unhappy_invalid_data" in names
        assert "SetSIPAccount_unhappy_wrong_type" in names
        assert "SetSIPAccount_unhappy_fuzz" in names

    def test_skips_endpoints_without_payloads(self, tmp_path):
        from config.json_generator import create_unhappy_tests

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            presets = create_unhappy_tests(
                ["/api/call/GetServiceCapabilities"],
                {},  # no payload for this endpoint
            )

        assert presets == []

    def test_creates_json_files_in_unhappy_folder(self, tmp_path):
        from config.json_generator import create_unhappy_tests

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            create_unhappy_tests(
                ["/api/call/SetSIPAccount"],
                {"SetSIPAccount": {"key": "val"}},
            )

        unhappy_files = list((tmp_path / "set" / "unhappy").rglob("*.json"))
        assert len(unhappy_files) == 4

    def test_increments_summary_counters(self, tmp_path):
        from config.json_generator import create_unhappy_tests, summary

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            create_unhappy_tests(
                ["/api/call/SetSIPAccount"],
                {"SetSIPAccount": {"key": "val"}},
            )

        assert summary["unhappy_no_data"] == 1
        assert summary["unhappy_invalid"] == 1
        assert summary["unhappy_wrong_type"] == 1
        assert summary["unhappy_fuzz"] == 1

    def test_json_file_paths_use_forward_slashes(self, tmp_path):
        from config.json_generator import create_unhappy_tests

        with patch("config.json_generator.JSON_FOLDER", tmp_path):
            presets = create_unhappy_tests(
                ["/api/call/SetSIPAccount"],
                {"SetSIPAccount": {"key": "val"}},
            )

        for preset in presets:
            assert "\\" not in preset["json_file"]


# ---------------------------------------------------------------------------
# Main function (integration-level)
# ---------------------------------------------------------------------------

class TestMain:
    def test_generates_presets_file(self, tmp_path):
        from config.json_generator import main

        presets_file = tmp_path / "presets.json"
        with (
            patch("config.json_generator.JSON_FOLDER", tmp_path / "json_configs"),
            patch("config.json_generator.PRESETS_FILE", presets_file),
        ):
            main()

        assert presets_file.exists()
        presets = json.loads(presets_file.read_text(encoding="utf-8"))
        assert isinstance(presets, list)
        assert len(presets) > 0

    def test_all_presets_have_required_keys(self, tmp_path):
        from config.json_generator import main

        presets_file = tmp_path / "presets.json"
        with (
            patch("config.json_generator.JSON_FOLDER", tmp_path / "json_configs"),
            patch("config.json_generator.PRESETS_FILE", presets_file),
        ):
            main()

        presets = json.loads(presets_file.read_text(encoding="utf-8"))
        required_keys = {"name", "endpoint", "json_file", "simple_format", "json_type"}
        for preset in presets:
            assert required_keys.issubset(preset.keys()), f"Missing keys in {preset['name']}"
