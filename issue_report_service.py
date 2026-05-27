from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from threading import Lock
from typing import Any

import requests
from openpyxl import Workbook, load_workbook


REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "issue_reports.xlsx"
REPORT_HEADERS = [
    "Timestamp UTC",
    "Molecule Query",
    "Report Type",
    "Message",
    "Contact",
    "Page URL",
    "User Agent",
]
GOOGLE_FORM_ENTRY_ENV = {
    "molecule_query": "GOOGLE_FORM_ENTRY_MOLECULE",
    "report_type": "GOOGLE_FORM_ENTRY_TYPE",
    "message": "GOOGLE_FORM_ENTRY_MESSAGE",
    "contact": "GOOGLE_FORM_ENTRY_CONTACT",
    "page_url": "GOOGLE_FORM_ENTRY_PAGE_URL",
    "user_agent": "GOOGLE_FORM_ENTRY_USER_AGENT",
}

_report_lock = Lock()


def save_issue_report(report: dict[str, Any]) -> dict[str, str]:
    row = _build_report_row(report)
    storage_mode = os.getenv("REPORT_STORAGE_MODE", "").strip().lower()
    google_form_action_url = os.getenv("GOOGLE_FORM_ACTION_URL", "").strip()

    if storage_mode == "google_form" or google_form_action_url:
        _save_issue_report_to_google_form(report)
        return {"destination": "google_form", "saved_to": google_form_action_url}

    saved_path = _save_issue_report_to_excel(row)
    return {"destination": "excel", "saved_to": str(saved_path)}


def _build_report_row(report: dict[str, Any]) -> list[str]:
    return [
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        str(report.get("molecule_query", "")),
        str(report.get("report_type", "")),
        str(report.get("message", "")),
        str(report.get("contact", "")),
        str(report.get("page_url", "")),
        str(report.get("user_agent", "")),
    ]


def _save_issue_report_to_google_form(report: dict[str, Any]) -> None:
    action_url = os.getenv("GOOGLE_FORM_ACTION_URL", "").strip()
    if not action_url:
        raise RuntimeError("GOOGLE_FORM_ACTION_URL is not configured.")

    missing_entries = [
        env_name
        for env_name in GOOGLE_FORM_ENTRY_ENV.values()
        if not os.getenv(env_name, "").strip()
    ]
    if missing_entries:
        missing = ", ".join(missing_entries)
        raise RuntimeError(f"Missing Google Form entry mappings: {missing}.")

    payload = {
        os.environ[env_name]: str(report.get(field_name, ""))
        for field_name, env_name in GOOGLE_FORM_ENTRY_ENV.items()
    }

    response = requests.post(action_url, data=payload, timeout=10)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Google Form rejected the report with status {response.status_code}."
        )


def _save_issue_report_to_excel(row: list[str]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with _report_lock:
        if REPORT_FILE.exists():
            workbook = load_workbook(REPORT_FILE)
            sheet = workbook.active
            if sheet.max_row == 0:
                sheet.append(REPORT_HEADERS)
        else:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Issue Reports"
            sheet.append(REPORT_HEADERS)

        sheet.append(row)

        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(
                max(max_length + 2, 14),
                60,
            )

        workbook.save(REPORT_FILE)

    return REPORT_FILE
