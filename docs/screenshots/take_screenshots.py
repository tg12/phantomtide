"""Screenshot script for Phantom Tide public docs.

Takes all screenshots needed for the public README, bypassing the
onboarding modal by injecting the localStorage key via add_init_script
so it is present before the page's own JS runs on every navigation.

Usage (run from any directory):
    python3 take_screenshots.py [--url http://localhost:8000] [--access-key YOUR_KEY]

Default URL: https://phantom.labs.jamessawyer.co.uk
Output: overwrites the PNG files in this directory.
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
DEFAULT_URL = "https://phantom.labs.jamessawyer.co.uk"
VIEWPORT = {"width": 1600, "height": 900}
DATA_WAIT_TIMEOUT_SECONDS = 45
DATA_WAIT_POLL_SECONDS = 5


def _dashboard_status(page: Page) -> dict[str, int | str]:
    """Return a small snapshot of dashboard hydration state."""
    return page.evaluate(
        """() => {
            const eventText = document.getElementById('hdrEventCount')?.textContent?.trim() || '--';
            const layerCounts = Array.from(document.querySelectorAll('[id^="layer-count-"]'))
              .map((el) => Number.parseInt((el.textContent || '0').replace(/,/g, ''), 10) || 0);
            const nonZeroLayerCounts = layerCounts.filter((value) => value > 0).length;
            const markerCount = document.querySelectorAll('.leaflet-marker-icon:not(.leaflet-marker-shadow)').length;
            return {
              eventText,
              nonZeroLayerCounts,
              markerCount,
            };
        }"""
    )


def wait_for_dashboard_data(page: Page, timeout_seconds: int = DATA_WAIT_TIMEOUT_SECONDS) -> None:
    """Wait for dashboard counts to hydrate, with terminal countdown output."""
    deadline = time.time() + timeout_seconds
    while True:
        status = _dashboard_status(page)
        event_text = str(status["eventText"])
        event_count = int(event_text.replace(",", "")) if event_text not in {"--", ""} and event_text.replace(",", "").isdigit() else 0
        non_zero_layer_counts = int(status["nonZeroLayerCounts"])
        marker_count = int(status["markerCount"])
        if event_count > 0 and (non_zero_layer_counts > 0 or marker_count > 0):
            print(
                f"  dashboard ready: {event_count} events, {non_zero_layer_counts} non-zero layer counts, {marker_count} markers"
            )
            return

        remaining = max(0, int(deadline - time.time()))
        print(
            f"  waiting for live data... {remaining:>3}s remaining "
            f"(events={event_text}, non-zero layers={non_zero_layer_counts}, markers={marker_count})"
        )
        if remaining == 0:
            print("  data wait timed out; continuing with best available dashboard state")
            return
        time.sleep(min(DATA_WAIT_POLL_SECONDS, remaining))


def enable_all_layers(page: Page) -> None:
    """Enable all available (non-disabled) layer checkboxes for screenshot capture."""
    toggled = page.evaluate(
        """() => {
            let toggled = 0;
            for (const cb of document.querySelectorAll('.layer-toggles input[data-layer]')) {
                if (!cb.disabled && !cb.checked) {
                    cb.click();
                    toggled += 1;
                }
            }
            return toggled;
        }"""
    )
    print(f"  enabled {toggled} additional layers")


def prime_dashboard(page: Page) -> None:
    """Turn on layers and wait for hydrated data. Does not click refresh to avoid re-triggering auth gates."""
    enable_all_layers(page)
    wait_for_dashboard_data(page)
    time.sleep(2.0)


def wait_for_map(page: Page, extra_sleep: float = 3.0) -> None:
    """Wait until the Leaflet map container is present, then pause for data."""
    page.wait_for_selector(".leaflet-container", timeout=30_000)
    try:
        page.wait_for_selector(
            ".leaflet-tile-loaded, .leaflet-marker-icon",
            timeout=10_000,
        )
    except Exception:
        pass
    time.sleep(extra_sleep)


def authenticate(page: Page, base_url: str, access_key: str) -> None:
    """POST the access key to the auth endpoint so the browser session is upgraded."""
    if not access_key:
        return
    auth_url = f"{base_url}/api/auth/session"
    result = page.evaluate(
        """async ([url, key]) => {
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({api_key: key})
                });
                return { status: res.status, ok: res.ok };
            } catch (e) {
                return { error: String(e) };
            }
        }""",
        [auth_url, access_key],
    )
    print(f"  auth: {result}")
    time.sleep(0.5)


def dismiss_modal(page: Page) -> None:
    """Force-hide any modal/gate backdrop so it never blocks pointer events."""
    dismissed = page.evaluate(
        """() => {
            let count = 0;
            // Hide all backdrop / dialog elements unconditionally
            for (const el of document.querySelectorAll(
                '.dialog-backdrop, .modal-backdrop, #onboarding-modal, [role="dialog"]'
            )) {
                el.style.setProperty('display', 'none', 'important');
                el.setAttribute('hidden', '');
                count += 1;
            }
            // Also inject a style rule so any dynamically created backdrops are also hidden
            if (!document.getElementById('_pt_ss_hide')) {
                const s = document.createElement('style');
                s.id = '_pt_ss_hide';
                s.textContent = '.dialog-backdrop { display: none !important; }';
                document.head.appendChild(s);
            }
            return count;
        }"""
    )
    if dismissed:
        print(f"  suppressed {dismissed} modal element(s)")


def go(page: Page, url: str, extra_sleep: float = 3.0, *, auth_key: str = "") -> None:
    """Navigate to URL and wait for the map. Onboarding is suppressed by init script."""
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    wait_for_map(page, extra_sleep=extra_sleep)
    if auth_key:
        authenticate(page, url, auth_key)
    dismiss_modal(page)
    prime_dashboard(page)


def take(page: Page, name: str) -> None:
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"  saved {path.name}")


def click_if_present(page: Page, selector: str, delay: float = 0.6) -> None:
    """Click the first matching element when present."""
    btn = page.query_selector(selector)
    if btn:
        btn.click()
        time.sleep(delay)


def run(base_url: str, access_key: str = "") -> None:
    global _access_key
    _access_key = access_key
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)

        # Inject onboarding-bypass keys before ANY page navigation.
        # Both v2 and the email-gate key are set to cover all gate checks.
        init_script = (
            "localStorage.setItem('pt:onboarding:v2', '1');"
            "localStorage.setItem('pt:email-gate:v2', '1');"
        )
        if _access_key:
            # Store access key under the key the app uses for session auth
            init_script += f"localStorage.setItem('pt:access-key:v1', '{_access_key}');"
        ctx.add_init_script(init_script)

        page = ctx.new_page()

        print(f"Target: {base_url}")
        print(f"Output: {OUT_DIR}\n")

        # --- 1. overview: full dashboard at world zoom ---
        print("overview")
        go(page, base_url, auth_key=_access_key)
        if page.evaluate("() => !document.getElementById('tables-panel')?.hidden"):
            click_if_present(page, "#btn-tables", delay=0.5)
        take(page, "overview")

        # --- 2. sidebar: layer control panel open ---
        print("sidebar")
        go(page, base_url, auth_key=_access_key)
        btn = page.query_selector("#layers-toggle, [aria-label*='layer' i], .layer-panel-toggle")
        if btn:
            btn.click()
            time.sleep(0.6)
        take(page, "sidebar")

        # --- 3. intel_tables: intel panel open with tables loaded ---
        print("intel_tables")
        go(page, base_url, auth_key=_access_key)
        click_if_present(page, "#btn-tables", delay=2.5)
        take(page, "intel_tables")

        # --- 4. source_health: health panel open ---
        print("source_health")
        go(page, base_url, auth_key=_access_key)
        click_if_present(page, "#source-health-toggle", delay=1.2)
        take(page, "source_health")

        # --- 5. detail_panel: click a marker to open detail ---
        print("detail_panel")
        go(page, base_url, auth_key=_access_key)
        page.evaluate("""() => {
            const markers = document.querySelectorAll('.leaflet-marker-icon:not(.leaflet-marker-shadow)');
            if (markers.length) markers[0].click();
        }""")
        time.sleep(1.0)
        take(page, "detail_panel")

        # --- 6. detail_panel_warning: click a nav-warning marker ---
        print("detail_panel_warning")
        go(page, base_url, auth_key=_access_key)
        page.evaluate("""() => {
            const markers = document.querySelectorAll('.leaflet-marker-icon');
            for (const m of markers) {
                const style = window.getComputedStyle(m);
                if (style.filter && style.filter.includes('hue')) { m.click(); return; }
            }
            const any = document.querySelector('.leaflet-marker-icon:not(.leaflet-marker-shadow)');
            if (any) any.click();
        }""")
        time.sleep(1.0)
        take(page, "detail_panel_warning")

        # --- 7. detail_panel_notam: open intel tables, click a NOTAM row ---
        print("detail_panel_notam")
        go(page, base_url, auth_key=_access_key)
        click_if_present(page, "#btn-tables", delay=2.5)
        page.evaluate("""() => {
            const rows = document.querySelectorAll('#notams-critical-table tr[data-idx]');
            if (rows.length) rows[0].click();
        }""")
        time.sleep(1.0)
        take(page, "detail_panel_notam")

        # --- 8. risk_zones: convergence layer visible ---
        print("risk_zones")
        go(page, base_url, auth_key=_access_key)
        page.evaluate("""() => {
            const cb = document.querySelector('input[data-layer="convergence"], input[data-layer="risk_zones"]');
            if (cb && !cb.checked) cb.click();
        }""")
        time.sleep(2.0)
        take(page, "risk_zones")

        # --- 9. weather_mesh: NDBC ocean state mesh ---
        print("weather_mesh")
        go(page, base_url, auth_key=_access_key)
        page.evaluate("void map.setView([45, -40], 4)")
        time.sleep(2.5)
        take(page, "weather_mesh")

        # --- 10. atlantic: regional view of North Atlantic ---
        print("atlantic")
        go(page, base_url, auth_key=_access_key)
        page.evaluate("void map.setView([40, -30], 4)")
        time.sleep(2.5)
        take(page, "atlantic")

        # --- 11. proximity_menu: right-click context menu ---
        print("proximity_menu")
        go(page, base_url, auth_key=_access_key)
        map_el = page.query_selector("#map")
        if map_el:
            bb = map_el.bounding_box()
            if bb:
                page.mouse.click(
                    bb["x"] + bb["width"] * 0.5,
                    bb["y"] + bb["height"] * 0.5,
                    button="right",
                )
                time.sleep(0.6)
        take(page, "proximity_menu")

        # --- 12. proximity_results: select a radius option ---
        print("proximity_results")
        page.evaluate("""() => {
            const items = document.querySelectorAll('.prox-menu-item');
            if (items.length > 1) items[1].click();
        }""")
        time.sleep(1.5)
        take(page, "proximity_results")

        # --- 13. sigmet_popup: click a SIGMET polygon to show plain-English popup (v1.44.0) ---
        print("sigmet_popup")
        go(page, base_url, auth_key=_access_key)
        # Enable SIGMET layer if not already on
        page.evaluate("""() => {
            const cb = document.querySelector('input[data-layer="sigmet"]');
            if (cb && !cb.checked && !cb.disabled) cb.click();
        }""")
        time.sleep(2.0)
        # Click the first SVG path (polygon layer) on the map
        clicked = page.evaluate("""() => {
            const paths = document.querySelectorAll('.leaflet-overlay-pane path');
            for (const p of paths) {
                p.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: 800, clientY: 450}));
                return true;
            }
            return false;
        }""")
        time.sleep(1.2)
        take(page, "sigmet_popup")

        # --- 14. entity_feed: entity feed intel table with watchlist hits (v1.44.0) ---
        print("entity_feed")
        go(page, base_url, auth_key=_access_key)
        # Enable entity feed layer
        page.evaluate("""() => {
            const cb = document.querySelector('input[data-layer="entity_feed"]');
            if (cb && !cb.checked && !cb.disabled) cb.click();
        }""")
        time.sleep(2.0)
        click_if_present(page, "#btn-tables", delay=2.5)
        # Scroll to entity feed table if present
        page.evaluate("""() => {
            const section = document.getElementById('entity-feed-section');
            if (section) section.scrollIntoView({behavior: 'instant', block: 'start'});
        }""")
        time.sleep(0.5)
        take(page, "entity_feed")

        # --- 15. middle_east: Middle East / Red Sea regional view for risk context ---
        print("middle_east")
        go(page, base_url, auth_key=_access_key)
        page.evaluate("void map.setView([20, 45], 5)")
        time.sleep(2.5)
        take(page, "middle_east")

        browser.close()
        print("\nDone.")


_access_key: str = ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Take Phantom Tide docs screenshots")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL of the running app")
    parser.add_argument("--access-key", default="", help="Access key to inject for premium tier screenshots")
    args = parser.parse_args()
    run(args.url.rstrip("/"), access_key=args.access_key)


if __name__ == "__main__":
    main()
