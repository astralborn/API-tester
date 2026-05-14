import sys
from pathlib import Path
from typing import Final

# ================= Resource Paths =================

def resource_path(relative_path: str) -> Path:
    """
    Return absolute path to a resource (JSON, presets, logs).
    Works for both Python scripts and frozen executables.
    """
    base_dir = (
        Path(sys.executable).parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent.parent  # src/
    )
    return base_dir / relative_path


# ================= Folders & Files =================

JSON_FOLDER: Final[Path] = resource_path("config/json_configs")
LOGS_FOLDER: Final[Path] = resource_path("logs")
PRESETS_FILE: Final[Path] = resource_path("config/presets.json")


# ================= Theme Colors =================

class LightTheme:
    BG: Final[str] = "#f0f0f0"
    ENTRY_BG: Final[str] = "#ffffff"
    TEXT_COLOR: Final[str] = "#000000"
    BTN_ACTIVE: Final[str] = "#d0d0d0"
    STATUS_BG: Final[str] = "#e0e0e0"


# ================= API Modes =================

JSON_TYPES: Final[list[str]] = [
    "Normal JSON",
    "Google JSON",
    "JSON-RPC",
]

METHOD_IN_OPTIONS: Final[list[str]] = [
    "Method in Path",
    "Method in Action",
    "Method in JSON Body",
]


# ================= API Endpoints =================

API_ENDPOINTS: Final[list[str]] = [
    # -------- Base --------
    "/api/call",
    "/api/intercom/",

    # -------- Contacts / Intercom --------
    "/api/intercom/GetContacts",
    "/api/intercom/SetContacts",
    "/api/intercom/RemoveContacts",

    # -------- SIP Accounts --------
    "/api/call/GetSIPAccount",
    "/api/call/GetSIPAccounts",
    "/api/call/SetSIPAccount",
    "/api/call/SetSIPAccounts",
    "/api/call/RemoveSIPAccount",
    "/api/call/RemoveSIPAccounts",
    "/api/call/GetSIPAccountStatus",

    # -------- Service / Capabilities --------
    "/api/call/GetServiceCapabilities",
    "/api/call/GetSupportedSIPAccountAttributes",
    "/api/call/GetSupportedSIPConfigurationAttributes",
    "/api/call/GetSIPConfiguration",
    "/api/call/SetSIPConfiguration",
    "/api/call/GetSupportedMediaEncryptionModes",

    # -------- Audio / Codecs --------
    "/api/call/GetDefaultAudioCodecs",
    "/api/call/GetSupportedAudioCodecs",
    "/api/call/GetAudioCodecs",
    "/api/call/SetAudioCodecs",

    # -------- Call Control --------
    "/api/call/Call",
    "/api/call/GetCallStatus",
    "/api/call/TerminateCall",
]
