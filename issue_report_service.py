from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

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

_report_lock = Lock()


def save_issue_report(report: dict[str, Any]) -> Path:
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

        sheet.append(
            [
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                report.get("molecule_query", ""),
                report.get("report_type", ""),
                report.get("message", ""),
                report.get("contact", ""),
                report.get("page_url", ""),
                report.get("user_agent", ""),
            ]
        )

        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(
                max(max_length + 2, 14),
                60,
            )

        workbook.save(REPORT_FILE)

    return REPORT_FILE
