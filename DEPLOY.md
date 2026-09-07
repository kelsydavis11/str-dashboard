# Deploying the STR dashboard (shareable URL)

Read-only Streamlit app over the `Confirmed Bookings` Google Sheet. This folder
is a self-contained deployable app (`app.py` + `data.py` / `metrics.py` /
`theme.py` / `calendar_view.py` + `requirements.txt` + `.streamlit/config.toml`).

Auth on the cloud comes from **Streamlit secrets** (not the local `token.json`):
the app reads `st.secrets` — a `[gcp_service_account]` table if present, else a
`[google_token]` table, else falls back to the local `token.json` for dev.

---

## 1. Put this folder on GitHub (personal account: kelsydavis11@gmail.com)

This folder is already a git repo with a commit. On https://github.com create a
**new empty repo** (e.g. `str-dashboard`, public is fine — no secrets are
committed), then from `~/booking-sync/dashboard`:

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/str-dashboard.git
git push -u origin main
```

If it asks for a password, use a **GitHub personal access token** (Settings →
Developer settings → tokens), not your account password. `.streamlit/secrets.toml`
is git-ignored, so your credentials are **not** pushed.

## 2. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in **with GitHub** (kelsydavis11).
2. **Create app** → pick the `str-dashboard` repo, branch `main`, main file
   `app.py`.
3. Before/after first deploy: **⋮ → Settings → Secrets**, and paste the contents
   of your local `.streamlit/secrets.toml` (already generated on your Mac with
   your token + sheet id). It looks like:

   ```toml
   GOOGLE_SHEET_ID = "…"

   [google_token]
   type = "authorized_user"
   client_id = "…"
   client_secret = "…"
   refresh_token = "…"
   ```

4. Save. The app builds and gives you a URL like
   `https://str-dashboard-<hash>.streamlit.app` — share that with your partner.

## 3. Keep it working

- **The pasted token can expire** (~7 days if the Google OAuth app is in
  "Testing" mode). If the app shows a Google auth error: run
  `node reauth-google.mjs` in `~/booking-sync`, then paste the new
  `refresh_token` into the Streamlit **Secrets** box.
- **Durable fix (set-and-forget):** switch to a **service account** — create one
  in Google Cloud Console, enable the Sheets API, download the JSON key, share
  the Sheet with its `client_email` as Viewer, and paste it under
  `[gcp_service_account]` in Secrets (see `secrets.toml.example`). Service-account
  keys don't expire.

## Notes

- **Public URL = public data.** Anyone with the link sees guest names, booking
  IDs and revenue. That's fine for a quick partner share; Streamlit's app
  settings can later restrict viewers by email if you want it private.
- The app is **read-only** — it never writes to the Sheet or touches the scraper.
- Server time on the cloud is UTC, so "today" may differ from Sydney by a few
  hours around midnight; harmless for this view.
