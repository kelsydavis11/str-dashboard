# Deploying the STR dashboard (shareable URL)

Read-only Streamlit app over the `Confirmed Bookings` Google Sheet. This folder is a self-contained deployable app (`app.py` + `data.py` / `metrics.py` / `theme.py` / `calendar_view.py` + `requirements.txt`).

Auth on the cloud comes from **Streamlit secrets** (not the local `token.json`): the app reads `st.secrets` — a `[gcp_service_account]` table if present, else a `[google_token]` table, else falls back to the local `token.json` for dev.

## Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in with the GitHub account that can access `kelsydavis11/str-dashboard`.
2. Create app → choose `kelsydavis11/str-dashboard`, branch `main`, main file `app.py`.
3. In app Settings → Secrets, add `GOOGLE_SHEET_ID` plus either a service account or Google authorized-user token.

Example using the existing Google token:

```toml
GOOGLE_SHEET_ID = "…"

[google_token]
type = "authorized_user"
client_id = "…"
client_secret = "…"
refresh_token = "…"
```

Recommended durable setup is a Google service account shared as Viewer on the STR Google Sheet:

```toml
GOOGLE_SHEET_ID = "…"

[gcp_service_account]
type = "service_account"
project_id = "…"
private_key_id = "…"
private_key = "-----BEGIN PRIVATE KEY-----\n…\n-----END PRIVATE KEY-----\n"
client_email = "…@….iam.gserviceaccount.com"
client_id = "…"
token_uri = "https://oauth2.googleapis.com/token"
```

The app is read-only and does not write to the Google Sheet.

## Privacy

This dashboard contains guest names, booking IDs and revenue. Keep the GitHub repository private and configure Streamlit access appropriately before sharing the app URL.
