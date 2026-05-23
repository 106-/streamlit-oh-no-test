# oh-no-test

A repository for deliberately reproducing the "Oh no. Error running app." state on Streamlit Cloud, used to validate external monitoring scripts.

Deployed at: <https://oh-no-page.streamlit.app/>

this may cause:

![Oh no. Error running app.](https://i.imgur.com/kv4a2sg.png)

## Why this exists

A Streamlit Cloud app can crash mid-run for various reasons (OOM, `SystemExit`, import errors, etc.), and the browser shows "Oh no. Error running app." We want to detect this from the outside, but standard HTTP-level monitoring does not work:

- **`/_stcore/health` is unusable.**
  On Streamlit Cloud, nginx falls back to serving the React SPA HTML shell for nearly every HTTP path including `/_stcore/health`. The endpoint never returns `ok`.

- **The WebSocket handshake HTTP status is not reliable either.**
  An upgrade request to `wss://.../_stcore/stream` returns a fake `HTTP 101` (with an HTML body and a missing `Sec-WebSocket-Accept` header) even when the app is showing "Oh no." A dead backend container and a live container whose script keeps crashing look identical at the HTTP layer.

- **The string `Oh no` is never sent by the server.**
  Streamlit is a CSR (client-side rendered) app. The initial HTML does not contain `Oh no`. The React frontend receives an error over WebSocket and renders the text into the DOM via JavaScript.

So the only reliable way to detect "Oh no" externally is **to run a real browser, execute the JavaScript, and inspect the resulting DOM.**

## Monitoring approach

Render the page with headless Chromium (Playwright) and check whether the string `Oh no.` is present in the DOM.

### Setup

```bash
uv sync
uv run playwright install chromium
```

### Run

```bash
# Pass a Streamlit Cloud subdomain
uv run python check.py oh-no-page

# Or pass a full URL
uv run python check.py https://your-app.streamlit.app/
```

The script exits with code 1 on DOWN and appends to `monitor.log`.

### cron example

```cron
*/5 * * * * cd /path/to/oh-no-test && uv run python check.py oh-no-page
```

## Toggling app behavior

To exercise both UP and DOWN paths of the monitoring script, `streamlit_app.py` switches behavior via Streamlit secrets.

In the Streamlit Cloud app settings, set the Secrets to:

```toml
# UP: small array, runs to completion
HUGE = false

# DOWN: tries to allocate a ~5 GiB numpy array, gets OOM-killed
HUGE = true
```

Streamlit Cloud restarts the app automatically when secrets change. With `HUGE = true`, running `check.py` should reproduce the same "Oh no" the browser sees.

## Files

- `streamlit_app.py` — the test app whose behavior is controlled by secrets
- `check.py` — Playwright-based monitoring script
- `pyproject.toml` / `uv.lock` — uv-managed dependencies
