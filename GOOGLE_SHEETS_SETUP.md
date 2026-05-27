# Google Sheet Issue Reports

The issue report form writes to Google Sheets when these Render environment variables are set:

```text
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account", ...}
GOOGLE_SHEET_WORKSHEET=Issue Reports
```

`GOOGLE_SHEET_WORKSHEET` is optional. If it is not set, the app uses `Issue Reports`.

## Setup

1. Create a Google Sheet.
2. Copy the Sheet ID from the URL:

   ```text
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```

3. Create a Google Cloud service account and generate a JSON key.
4. Share the Google Sheet with the service account email. Give it Editor access.
5. In Render, open the Web Service settings and add:
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON`
   - optional: `GOOGLE_SHEET_WORKSHEET`
6. Redeploy the Render service.

If Google Sheet settings are missing, the app falls back to local Excel logging at:

```text
reports/issue_reports.xlsx
```

Render's local file storage is not reliable for long-term records, so Google Sheets should be used for production.
