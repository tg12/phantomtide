"""Automated screenshot script for Phantom Tide public docs.

Authenticates via the access-key API, suppresses all modals via CSS,
and captures all shots without any user interaction.

Usage:
    python3 take_screenshots_auto.py --access-key YOUR_KEY [--url URL]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import Page, sync_playwright
except ImportError:
    print("playwright not installed — run: pip install playwright && playwright install chromium")
    sys.exit(1)

OUT_DIR = Path(__file__).parent
DEFAULT_URL = "http://localhost:8000"
VIEWPORT = {"width": 1600, "height": 900}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def take(page: Page, name: str) -> None:
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"  [saved] {path.name}")


def suppress_modals(page: Page) -> None:
    """Inject CSS to hide blocking gate/auth dialogs during capture."""
    page.evaluate("""() => {
        if (document.getElementById('_pt_no_modal')) return;
        const s = document.createElement('style');
        s.id = '_pt_no_modal';
        s.textContent = `
            #onboarding-modal,
            #confirm-dialog,
            #auth-dialog { display: none !important; }
        `;
        document.head.appendChild(s);
    }""")


def authenticate(page: Page, base_url: str, key: str) -> bool:
    """POST the access key to the auth endpoint and return True on success."""
    result = page.evaluate(
        """async ([url, k]) => {
            try {
                const r = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({api_key: k}),
                });
                const body = await r.json().catch(() => ({}));
                return {status: r.status, ok: r.ok, tier: body.tier ?? null};
            } catch (e) {
                return {error: String(e)};
            }
        }""",
        [f"{base_url}/api/auth/session", key],
    )
    ok = result.get("ok", False)
    print(f"  auth → status={result.get('status')} tier={result.get('tier')} ok={ok}")
    return ok


def enable_layers(page: Page) -> int:
    return page.evaluate("""() => {
        let n = 0;
        for (const cb of document.querySelectorAll('.layer-toggles input[data-layer]')) {
            if (!cb.disabled && !cb.checked) { cb.click(); n++; }
        }
        return n;
    }""")


def wait_data(page: Page, seconds: int = 15) -> None:
    """Poll until event count is non-zero or timeout."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        ev = page.evaluate(
            "() => document.getElementById('hdrEventCount')?.textContent?.trim() || '--'"
        )
        if ev not in {"--", "0", ""}:
            print(f"  data ready — events={ev}")
            return
        remaining = int(deadline - time.time())
        print(f"  waiting... events={ev} ({remaining}s left)")
        time.sleep(2)
    print("  data wait timed out, proceeding")


def load(page: Page, base_url: str, key: str, zoom: tuple[float, float, int] | None = None) -> None:
    """Navigate, authenticate, suppress modal, enable layers, wait for data."""
    page.goto(base_url, wait_until="domcontentloaded", timeout=60_000)
    try:
        page.wait_for_selector(".leaflet-container", timeout=20_000)
    except Exception:
        pass
    time.sleep(0.8)
    suppress_modals(page)
    if key:
        authenticate(page, base_url, key)
    time.sleep(0.5)
    n = enable_layers(page)
    print(f"  enabled {n} layers")
    if zoom:
        lat, lon, z = zoom
        page.evaluate(f"void map.setView([{lat}, {lon}], {z})")
        time.sleep(0.8)
    wait_data(page)
    time.sleep(1.0)


# ---------------------------------------------------------------------------
# Screenshot sequence
# ---------------------------------------------------------------------------

def run(base_url: str, key: str) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        # Bypass gate keys before any JS runs
        ctx.add_init_script(
            "localStorage.setItem('pt:onboarding:v2','1');"
            "localStorage.setItem('pt:email-gate:v2','1');"
        )
        page = ctx.new_page()

        print(f"\nTarget : {base_url}")
        print(f"Output : {OUT_DIR}\n")

        # ------------------------------------------------------------------
        # 1. overview — world zoom, all layers on
        # ------------------------------------------------------------------
        print("1/16  overview")
        load(page, base_url, key)
        # close intel panel if open
        if not page.evaluate("() => document.getElementById('tables-panel')?.hidden ?? true"):
            page.evaluate("() => document.getElementById('btn-tables')?.click()")
            time.sleep(0.4)
        take(page, "overview")

        # ------------------------------------------------------------------
        # 2. sidebar — layer panel open
        # ------------------------------------------------------------------
        print("2/16  sidebar")
        load(page, base_url, key)
        page.evaluate("""() => {
            const btn = document.querySelector(
                '#layers-toggle, [aria-label*="layer" i], .layer-panel-toggle'
            );
            if (btn) btn.click();
        }""")
        time.sleep(0.8)
        take(page, "sidebar")

        # ------------------------------------------------------------------
        # 3. intel_tables — tables panel open
        # ------------------------------------------------------------------
        print("3/16  intel_tables")
        load(page, base_url, key)
        page.evaluate("() => document.getElementById('btn-tables')?.click()")
        time.sleep(1.5)
        take(page, "intel_tables")

        # ------------------------------------------------------------------
        # 4. source_health
        # ------------------------------------------------------------------
        print("4/16  source_health")
        load(page, base_url, key)
        page.evaluate("() => document.getElementById('source-health-toggle')?.click()")
        time.sleep(0.8)
        take(page, "source_health")

        # ------------------------------------------------------------------
        # 5. detail_panel — click first available marker
        # ------------------------------------------------------------------
        print("5/16  detail_panel")
        load(page, base_url, key)
        page.evaluate("""() => {
            const m = document.querySelector(
                '.leaflet-marker-icon:not(.leaflet-marker-shadow)'
            );
            if (m) m.click();
        }""")
        time.sleep(0.8)
        take(page, "detail_panel")

        # ------------------------------------------------------------------
        # 6. detail_panel_warning — prefer a coloured/advisory marker
        # ------------------------------------------------------------------
        print("6/16  detail_panel_warning")
        load(page, base_url, key)
        page.evaluate("""() => {
            const all = Array.from(document.querySelectorAll('.leaflet-marker-icon'));
            const advisory = all.find(m => {
                const f = window.getComputedStyle(m).filter;
                return f && f !== 'none';
            });
            (advisory || all[0])?.click();
        }""")
        time.sleep(0.8)
        take(page, "detail_panel_warning")

        # ------------------------------------------------------------------
        # 7. detail_panel_notam — open tables, click first NOTAM row
        # ------------------------------------------------------------------
        print("7/16  detail_panel_notam")
        load(page, base_url, key)
        page.evaluate("() => document.getElementById('btn-tables')?.click()")
        time.sleep(1.5)
        page.evaluate("""() => {
            const row = document.querySelector('#notams-critical-table tr[data-idx]');
            if (row) row.click();
        }""")
        time.sleep(0.8)
        take(page, "detail_panel_notam")

        # ------------------------------------------------------------------
        # 8. risk_zones — convergence heat cells
        # ------------------------------------------------------------------
        print("8/16  risk_zones")
        load(page, base_url, key)
        page.evaluate("""() => {
            const cb = document.querySelector(
                'input[data-layer="convergence"], input[data-layer="risk_zones"]'
            );
            if (cb && !cb.checked && !cb.disabled) cb.click();
        }""")
        time.sleep(1.5)
        take(page, "risk_zones")

        # ------------------------------------------------------------------
        # 9. weather_mesh — NDBC North Atlantic
        # ------------------------------------------------------------------
        print("9/16  weather_mesh")
        load(page, base_url, key, zoom=(45, -40, 4))
        take(page, "weather_mesh")

        # ------------------------------------------------------------------
        # 10. atlantic — regional North Atlantic
        # ------------------------------------------------------------------
        print("10/16  atlantic")
        load(page, base_url, key, zoom=(40, -30, 4))
        take(page, "atlantic")

        # ------------------------------------------------------------------
        # 11. proximity_menu — right-click context menu
        # ------------------------------------------------------------------
        print("11/16  proximity_menu")
        load(page, base_url, key)
        box = page.query_selector("#map")
        if box:
            bb = box.bounding_box()
            if bb:
                page.mouse.click(
                    bb["x"] + bb["width"] * 0.5,
                    bb["y"] + bb["height"] * 0.5,
                    button="right",
                )
                time.sleep(0.6)
        take(page, "proximity_menu")

        # ------------------------------------------------------------------
        # 12. proximity_results — click first radius option
        # ------------------------------------------------------------------
        print("12/16  proximity_results")
        page.evaluate("""() => {
            const items = document.querySelectorAll('.prox-menu-item');
            if (items.length > 1) items[1].click();
            else if (items.length) items[0].click();
        }""")
        time.sleep(1.5)
        take(page, "proximity_results")

        # ------------------------------------------------------------------
        # 13. sigmet_popup — click a SIGMET polygon (v1.44.0)
        # ------------------------------------------------------------------
        print("13/16  sigmet_popup")
        load(page, base_url, key)
        page.evaluate("""() => {
            const cb = document.querySelector('input[data-layer="sigmet"]');
            if (cb && !cb.checked && !cb.disabled) cb.click();
        }""")
        time.sleep(1.5)
        page.evaluate("""() => {
            const path = document.querySelector('.leaflet-overlay-pane path');
            if (path) {
                const bb = path.getBoundingClientRect();
                const cx = bb.left + bb.width / 2;
                const cy = bb.top + bb.height / 2;
                path.dispatchEvent(new MouseEvent('click', {
                    bubbles: true, cancelable: true,
                    clientX: cx, clientY: cy
                }));
            }
        }""")
        time.sleep(0.8)
        take(page, "sigmet_popup")

        # ------------------------------------------------------------------
        # 14. entity_feed — watchlist hits intel table (v1.44.0)
        # ------------------------------------------------------------------
        print("14/16  entity_feed")
        load(page, base_url, key)
        page.evaluate("""() => {
            const cb = document.querySelector('input[data-layer="entity_feed"]');
            if (cb && !cb.checked && !cb.disabled) cb.click();
        }""")
        time.sleep(1.0)
        page.evaluate("() => document.getElementById('btn-tables')?.click()")
        time.sleep(1.5)
        page.evaluate("""() => {
            const s = document.getElementById('entity-feed-section');
            if (s) s.scrollIntoView({behavior: 'instant', block: 'start'});
        }""")
        time.sleep(0.4)
        take(page, "entity_feed")

        # ------------------------------------------------------------------
        # 15. middle_east — Red Sea / Persian Gulf
        # ------------------------------------------------------------------
        print("15/16  middle_east")
        load(page, base_url, key, zoom=(20, 45, 5))
        take(page, "middle_east")

        # ------------------------------------------------------------------
        # 16. aircraft_search — quick jump modal (v1.72.0)
        # ------------------------------------------------------------------
        print("16/16  aircraft_search")
        load(page, base_url, key)
        page.keyboard.press("/")
        time.sleep(0.8)
        page.fill("#aircraft-search-input", "air")
        time.sleep(0.8)
        take(page, "aircraft_search")

        # ------------------------------------------------------------------
        browser.close()
        print("\nComplete. Screenshots saved:")
        for p in sorted(OUT_DIR.glob("*.png")):
            print(f"  {p.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated Phantom Tide screenshot capture")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL of the running app")
    parser.add_argument("--access-key", default="", help="Access key for premium tier")
    args = parser.parse_args()
    run(args.url.rstrip("/"), args.access_key)


if __name__ == "__main__":
    main()
