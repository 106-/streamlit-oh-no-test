"""
Liveness check for a Streamlit Cloud app (Playwright-based).

HTTP-level probes cannot reliably detect "Oh no. Error running app.":
- Streamlit Cloud is CSR, so the initial HTML never contains "Oh no".
- The WebSocket handshake returns a misleading fake 101.
- Script-crash failures still let the handshake appear to succeed.

So we render the page in headless Chromium and look for the "Oh no" string in the DOM.

Run:  uv run python check.py <subdomain-or-url>
      uv run python check.py oh-no-page
      uv run python check.py https://oh-no-page.streamlit.app/
cron: */5 * * * * cd /path/to/script/oh-no-test && uv run python check.py oh-no-page
"""

import argparse
import sys
import asyncio
import logging
import pathlib
from playwright.async_api import async_playwright

LOG = pathlib.Path(__file__).parent / "monitor.log"

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("oh-no-check")


def resolve_url(arg: str) -> str:
    """Accept either a full URL or a Streamlit Cloud subdomain."""
    if arg.startswith(("http://", "https://")):
        return arg
    return f"https://{arg}.streamlit.app/"


async def check(url: str) -> tuple[str, str]:
    """Return (status, detail). status is "UP" or "DOWN"."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for JS execution, WebSocket connect, initial messages, DOM render
            await asyncio.sleep(5)

            oh_no = await page.locator("text=Oh no.").count()
            if oh_no > 0:
                body = await page.evaluate("() => document.body.innerText.slice(0, 200)")
                detail = body.replace("\n", " ").strip()
                return "DOWN", f'"Oh no" detected: "{detail}"'
            return "UP", '"Oh no" not present'
        finally:
            await browser.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Liveness check for a Streamlit Cloud app (Playwright-based)."
    )
    parser.add_argument(
        "target",
        help="Streamlit Cloud subdomain (e.g. 'oh-no-page') or a full URL",
    )
    args = parser.parse_args()
    url = resolve_url(args.target)

    try:
        status, detail = await check(url)
    except Exception as e:
        status, detail = "DOWN", f"check failed: {type(e).__name__}: {e}"

    if status == "DOWN":
        logger.warning("%s %s", url, detail)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
