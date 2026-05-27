# Google Form Issue Reports

The issue report form can send reports to a Google Form without Google Cloud,
service accounts, or JSON keys.

## 1. Create The Google Form

Create a Google Form with these fields:

1. `Related molecule` - Short answer
2. `Problem type` - Short answer or dropdown
3. `Message` - Paragraph
4. `Contact` - Short answer
5. `Page URL` - Short answer
6. `User Agent` - Short answer

In the Google Form Responses tab, link responses to a Google Sheet.

## 2. Get The Form Action URL And Entry IDs

Open the published Google Form, then view the page source.

Find the form action URL. It should look like:

```text
https://docs.google.com/forms/d/e/FORM_ID/formResponse
```

Find each field name. Google Forms fields look like:

```text
entry.123456789
```

Map each field to the matching Render environment variable.

## 3. Render Environment Variables

Set these in Render:

```text
REPORT_STORAGE_MODE=google_form
GOOGLE_FORM_ACTION_URL=https://docs.google.com/forms/d/e/1FAIpQLSfOhogo69jm-AcOhH0PSzCEsVY3SiIRkt9hOh9JK8I5iy278Q/formResponse
GOOGLE_FORM_ENTRY_MOLECULE=entry.777196847
GOOGLE_FORM_ENTRY_TYPE=entry.2089935924
GOOGLE_FORM_ENTRY_MESSAGE=entry.511587003
GOOGLE_FORM_ENTRY_CONTACT=entry.730782396
GOOGLE_FORM_ENTRY_PAGE_URL=entry.2109422454
GOOGLE_FORM_ENTRY_USER_AGENT=entry.437465040
```

The app keeps the same `/api/report` endpoint. If the Google Form variables are
not configured, local development falls back to:

```text
reports/issue_reports.xlsx
```

On Render, `REPORT_STORAGE_MODE=google_form` makes missing Google Form settings
fail clearly instead of silently writing to temporary local storage.

If the app receives a 401 response from Google Forms, open the Google Form
settings and turn off options that require sign-in, restrict responses to an
organization, or limit users to one response.
