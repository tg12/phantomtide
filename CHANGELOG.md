# Changelog

All notable internal changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

Public-safe release notes live in `../phantomtide/CHANGELOG.md`.

Release hygiene:
- `phantom-tide` is the internal code repo.
- `../phantomtide` is the public docs repo.
- When cutting a new release, sync both repos' README and CHANGELOG files in the same pass.

## [Unreleased] — v1.45.0

### Track A — Debt
- Redis recovery procedure: write and validate `project-planning/REDIS_RECOVERY.md`
  distinguishing cache loss from archive loss; test against live stack.

### Track B — Performance
- Split `frontend/js/app.js` (~12,500+ lines) at the data-loading / rendering
  seam into `data.js`, `render.js`, and a slimmed `app.js` bootstrap.
  Each file under 5,000 lines.  Biome lint passes on all three.

### Track C — Features
- Watchlist alert panel: sidebar panel listing every on-map entity matching
  the vessel or aircraft watchlists, sorted by last seen, clickable to jump.
  Entity feed corroboration badge shown when present.  Frontend-only; updates
  each refresh cycle.

Full triage and acceptance criteria: `project-planning/V1_45_TRIAGE.md`.
Delivery model: `project-planning/FORWARD_ROADMAP.md`.

---

## v1.44.0 — 2026-04-05

### Performance — static layer pre-serialization (Track B)

All 8 maritime reference layer loaders in `api/routes/static_layers.py` now
pre-serialize to `bytes` via `core.json_utils.dumps_bytes()` (orjson) inside
their `@lru_cache(maxsize=1)` call, cached once per process lifetime:

- `_load_submarine_cables`, `_load_vessel_routing`, `_load_maritime_regions`,
  `_load_exploration_areas`, `_load_marine_transport`, `_load_danger_zones`,
  `_load_lightening_zones`, `_load_anchorages`

Routes now return `Response(content=bytes, media_type="application/json")`
instead of `JSONResponse(dict)`, eliminating `json.dumps()` on every request.
Sub-loaders `_load_marine_transport_lanes()` / `_load_marine_transport_channels()`
remain `dict`-returning as they feed the merge function.

### Performance — ETag/304 on `/api/events/geojson` (Track B)

- `api/routes/events.py`: cached byte payloads now carry an ETag header
  computed as `sha256(bytes)[:16]`.  When the frontend sends `If-None-Match`
  matching the current ETag, the route returns 304 and skips deserialization
  and re-render on the client.
- `import hashlib` added; response path unchanged when cache misses or revision
  changes.

### Performance — entity feed concurrency and Docker logging (Track B)

- `frontend/js/app.js`: `loadEntityFeedVessels()` and `loadEntityFeedAircraft()`
  removed from the constant `auxiliaryTasks` array.  Previously they consumed
  2 of 4 `REFRESH_AUX_CONCURRENCY` slots on every 30-second cycle despite the
  backend only refreshing the feed every 10 minutes.  Both calls now fire-and-
  forget after the main `await Promise.all(...)`, guarded by
  `shouldRefreshTask("entityFeed", 10 * 60_000, force)`.  Watchlist hits fetch
  and highlight re-render are chained in the same 10-min block.
- `docker-compose.yml`: app service now uses `logging: driver: "local"` with
  `max-size: 50m / max-file: 5`.  Eliminates synchronous json-file write
  overhead incurred on every `logger.*()` call under the default driver.

### SIGMET popup — plain-English rendering and centroid fix

- `renderLayer()`: Added `const isSigmet = source === "sigmet"` flag.  SIGMET
  centroid markers now dispatch to `sigmetPopupHtml()` instead of falling
  through to `popupHtml()`.  The generic fallback was dumping every attribute
  key including the raw GeoJSON `geometry` blob (converted to a JSON string).
- `renderSigmetPolygons()`: polygon hover tooltip upgraded from the raw hazard
  code (`TS`) to `OEJD FIR · Thunderstorm` using the existing lookup tables.
- `sigmetPopupHtml()`:
  - `_SIGMET_SEVERITY_LABELS` lookup added: `LGT/MOD/SEV/EXTREME` →
    `Light/Moderate/Severe/Extreme`; displayed as an "Intensity" row in the
    meta section when `attrs.severity` is present.
  - Collapsible "Raw bulletin" `<details>` block added, sourced from
    `raw_value.raw_text` (the original AVMET text), hidden by default.

### Supplemental Entity Feed layer (new premium feature)

A new premium-gated toggle "Supplemental Entity Feed" in the sidebar sidebar
activates two complementary views:

**Map highlight overlay** (`renderEntityFeedHighlights()`):

- Scans `_eventIndex` once per entity feed refresh (every 10 min) to build
  an MMSI/ICAO24 → `{lat, lon}` lookup; O(n) over live events.
- For each entity in `state.entityFeedVessels` / `state.entityFeedAircraft`
  that has a matching live AIS/OpenSky marker, adds a `L.circleMarker` ring
  to `state.entityFeedHighlightLayer`.
- Red ring (radius 14, weight 2.5) = watchlist hit; cyan ring (radius 10,
  weight 1.5) = general corroboration.  `interactive: false` — clicks pass
  through to the underlying marker.
- Ring positions update every 30-second cycle as AIS/OpenSky markers move,
  even when the entity feed data itself has not changed.
- Inline note below the toggle shows hit count and watchlist hit summary.

**Intel table** (`renderEntityFeedTable()`):

- New "Entity Feed — Watchlist Hits" section in the Intel Tables panel.
- Columns: Type | Name/Callsign | ID (MMSI/ICAO24) | Observation count |
  Last Seen | Live (`ON MAP` / `off map` from a real-time coord index check).
- Sourced from `/api/entity_feed/watchlist_hits` — only entities that are
  both in the feed and matched by `get_vessel_match()` / `get_aircraft_match()`.
- Loaded as part of `loadIntelTables()` and also in the 10-min fire-and-forget
  entity feed refresh block.

**Wiring**:

- `API.entityFeedWatchlistHits` URL constant added.
- `state.entityFeedWatchlistHits: { vessels: [], aircraft: [] }` added.
- `loadEntityFeedWatchlistHits()` fetches the hits endpoint; premium-gated.
- `_buildEntityIdentifierCoordIndex()` helper: single O(n) scan of
  `_eventIndex` returning `Map<mmsi/icao24, {lat, lon}>`.
- `_entityFeedRingMarkers: Map<id, CircleMarker>` module-level cache.
- Toggle change handler re-renders highlights and table immediately.
- `entity_feed` feature registered in `FEATURE_TIER_REGISTRY` as `"premium"`.

### Tier gating — FEATURE_TIER_REGISTRY and bug fixes

**CSS bug fix** — `api/routes/static_layers.py` tier badges visible for
premium users:

- Root cause: `.layer-unavailable-tag { display: inline-block }` in
  `frontend/css/style.css` overrode the UA stylesheet's `display:none` for
  elements with the HTML `[hidden]` attribute.  `premiumTag.hidden = true`
  from JS was silently ignored.
- Fix: `.layer-unavailable-tag[hidden] { display: none; }` added to
  `style.css`.  Class + attribute specificity beats the class-only rule.

**Registry drift bug fix** — starter tier access to danger/lightering/anchorage
layers:

- `danger_zones`, `lightening_zones`, `anchorages` were in
  `PREMIUM_ONLY_TOGGLE_CONTROLS` but absent from
  `STARTER_PREMIUM_ONLY_FEATURES_DEFAULT`.  Consequence: starter users could
  call their API endpoints and render their map layers, and the `locked`
  computation in `updatePremiumOnlyToggleControls()` was incorrect for all
  tiers.

**FEATURE_TIER_REGISTRY — single source of truth**:

- Replaced the manually-maintained `STARTER_PREMIUM_ONLY_FEATURES_DEFAULT`
  array and `ENTERPRISE_ONLY_FEATURES_DEFAULT` array with a single
  `const FEATURE_TIER_REGISTRY` mapping all 19 gated `featureId` strings to
  their minimum tier (`"premium"` or `"enterprise"`).
- Both arrays are now derived:
  ```
  STARTER_PREMIUM_ONLY_FEATURES_DEFAULT =
    Object.entries(FEATURE_TIER_REGISTRY)
      .filter(([, tier]) => tier === "premium" || tier === "enterprise")
      .map(([id]) => id);
  ```
- Adding a new gated feature requires one line in the registry; all check
  points (`isStarterPremiumOnlyFeatureLocked`, `isEnterpriseFeatureLocked`,
  `updatePremiumOnlyToggleControls`, API guards) pick it up automatically.
- `Object.entries(FEATURE_TIER_REGISTRY)` in the browser console gives the
  complete tier manifest for audit.

### Vulture dead-code audit — whitelist updated

13 false positives added to `whitelist_vulture.py`:

- `sync_api_runtime_state` — FastAPI `@app.middleware("http")` handler
- `entity_feed_vessels`, `entity_feed_aircraft`, `entity_feed_watchlist_hits`
  — `@router.get` handlers in `api/routes/entity_feed.py`
- `event_timeline` — `api/routes/events.py`
- `vessel_history`, `aircraft_history` — `api/routes/history.py`
- `ports`, `danger_zones`, `lightening_zones`, `anchorages` — `api/routes/static_layers.py`
- `get_version` — `api/routes/version.py`
- `ais_vessel_zone_alerts` — `api/routes/vessels.py`

All are FastAPI route handlers or middleware functions called by framework
dispatch, not by direct Python reference.

### Tests

- `test_exploration_areas_route_returns_features`: monkeypatched loader now
  returns `json.dumps(payload).encode()` (bytes) to match the updated loader
  return type.  Test was returning a `dict`, causing a 500 from `Response`.
- `test_danger_zones_route_returns_features` — new
- `test_lightening_zones_route_returns_features` — new
- `test_anchorages_route_returns_features` — new
- Suite: **440 passed** (was 436 before this session).  4 pre-existing
  failures in `tests/test_sanitize_live_ais_ports.py` reference a missing
  `tools/sanitize_live_ais_ports.py` — unrelated to this release.

---

## v1.43.0 — 2026-04-05

### AviationWeather SIGMET collector

- New `collectors/aviationweather/sigmet_collector.py` fetches US convective
  SIGMETs (`/api/data/sigmet`) and international SIGMETs (`/api/data/isigmet`)
  from AviationWeather.gov.  No authentication required.  GeoJSON feed.
- 20-minute rolling replace via REF_SOURCES (atomic snapshot semantics).
- Both feeds attempted independently; feed failure falls back to
  `data/sigmet_cache.json` without blocking the other.
- `_centroid()` computes approximate lat/lon from Polygon/MultiPolygon/Point
  geometry; full geometry dict stored in `attributes.geometry` for frontend
  polygon rendering.
- Expired events (past `valid_until`) are dropped before cache write.
- `_MARITIME_RELEVANT_HAZARDS = {CONVECTIVE, TS, VA, TURB, DS, TROPICAL_CYCLONE, MTW}`
  — each feature carries a `maritime_relevant` boolean for frontend filtering.
- `core/constants.py`: `SRC_SIGMET`, `ET_SIGMET`, `SIGMET_US_URL`,
  `SIGMET_INTL_URL` added; `ET_SIGMET` included in `ALL_EVENT_TYPES`.
- `core/store.py`: `"sigmet"` added to `REF_SOURCES`.
- `api/scheduler.py`: `SigmetCollector` registered with 20-minute interval,
  startup run enabled.
- `api/app.py`: sigmet added to `_REF_PRELOADS`.
- Frontend: `data-layer="sigmet"` toggle added to layer panel; `SOURCE_COLORS`
  (red-600), `SOURCE_SHAPES` (shield), `STALE_THRESHOLDS` (25 min),
  `EVENT_REFRESH_INTERVALS` (20 min), `SOURCE_DISPLAY_NAMES` wired.
  `sigmetPopupHtml()` renders hazard chip by type (TS/VA/TURB/DS each
  colour-coded), maritime-relevance tag, movement, altitude ceiling, valid
  window, and raw SIGMET text.  `renderSigmetPolygons()` reads
  `attributes.geometry` and renders filled, semi-transparent hazard polygons
  into the sigmet layer group alongside the centroid pin marker; viewport-culled.

### Entity history API (vessel and aircraft track history)

- New `core/ch_store.py:load_entity_history(identifier, source, hours, limit)`:
  queries ClickHouse by `source + mmsi` for the last N hours of positional
  data; converts OpenSky velocity (m/s) to knots; returns oldest-first list of
  `{lat, lon, timestamp, speed_kts}`.
- New `api/routes/history.py` router at `/api/history`:
  - `GET /api/history/vessel/{mmsi}?hours=24&limit=500`
  - `GET /api/history/aircraft/{icao24}?hours=24&limit=500`
  Starter tier returns empty `points` list with `"tier":"starter"` field — no
  HTTP error, no broken state in the frontend.  Premium+ calls
  `load_entity_history()`.  Bounds: `hours` capped at 168, `limit` at 2000.
- `api/app.py`: `history_router` registered at `/api/history`.
- Frontend: `API.vesselHistory(mmsi, hours)` and `API.aircraftHistory(icao24,
  hours)` constants added.  `loadAndShowTrackHistory(id, source)` fetches the
  endpoint and renders a fading polyline into `state.activeTrackLayer`: opacity
  scales linearly from 0.15 (oldest segment) to 0.80 (most recent), colour
  matches source (blue=AIS, violet=OpenSky).  Per-segment tooltip shows UTC
  timestamp and speed.  Start marker rendered at oldest point.
  `clearTrackHistory()` removes the polyline.  "Show track" / "Hide track"
  button injected into AIS and OpenSky detail panels; toggle is idempotent.

### New NOAA static maritime layers

Three additional ArcGIS FeatureServer sources added to
`scripts/fetch_maritime_layers.py` and `api/routes/static_layers.py`:

| Source key         | Output file                   | Features | Layer type       | Intel value |
|--------------------|-------------------------------|----------|------------------|-------------|
| `danger_zones`     | `noaa_danger_zones.json`      | 422      | `restricted_area`| Military exclusion zones; AIS gap inside = explained anomaly |
| `lightening_zones` | `noaa_lightening_zones.json`  | 122      | `lightening_zone`| STS transfer areas; sanctioned tanker loitering = illicit transfer signal |
| `anchorages`       | `noaa_anchorages.json`        | 679      | `anchorage`      | Dwell outside designated anchorage = deviation from expected behaviour |

- All three served by new `GET /api/static/danger-zones`,
  `/lightening-zones`, `/anchorages` routes (premium tier).
- Cached loaders follow the existing `@lru_cache(maxsize=1) + _load_optional_json`
  pattern; empty `FeatureCollection` returned if the file has not been fetched.
- Frontend: toggle rows added to the premium static layers panel for all three.
  Shared `_renderNoaaPolygonLayer()` helper renders viewport-culled polygons
  with source-appropriate stroke colours (red=restricted, amber=lightering,
  teal=anchorage); lazy-loaded on first toggle enable; re-rendered on zoom/move.
  Bootstrap static restore includes all three when toggled on.
- Module docstring updated to list all three new routes.

### Entity feed integration

- New `collectors/entity_feed/entity_feed_fetcher.py` module fetches two
  supplemental identity feeds (vessel MMSI and aircraft ICAO24) from an
  external host on a 10-minute scheduler interval.  15-second per-feed timeout.
  Both feeds are attempted independently; failure on one does not block the other.
- Module-level in-memory cache (dicts keyed by MMSI / ICAO24) is refreshed by
  the scheduler job and preloaded from `data/entity_feed_cache.json` at startup.
- `api/routes/entity_feed.py` — three new endpoints (premium tier):
  - `GET /api/entity_feed/vessels` — full vessel entity list
  - `GET /api/entity_feed/aircraft` — full aircraft entity list
  - `GET /api/entity_feed/watchlist_hits` — intersection with
    `get_vessel_match()` / `get_aircraft_match()`; each hit carries the entity
    feed record merged with the matched watchlist record
- `api/scheduler.py` — `_run_entity_feed_slow()` job registered at 10-minute
  interval with an immediate startup run.  After refreshing the cache the job
  calls `emit_watchlist_hit_hypotheses()` to push flagged-entity-active signals
  to the store hypothesis deque (threshold: `seconds_from_now < 7200`).
- `api/app.py` — `_preload_entity_feed()` warms the in-memory cache from the
  file cache before the scheduler runs.  `entity_feed_router` registered at
  `/api/entity_feed`.
- Frontend: `state.entityFeedVessels` and `state.entityFeedAircraft` populated
  each refresh cycle via `loadEntityFeedVessels()` / `loadEntityFeedAircraft()`.
  Both are non-fatal — missing data or access-tier denial retains the existing
  cache and does not interrupt the refresh cycle.
- `entityFeedBadgeHtml()` helper renders a compact "Entity feed: N obs, last
  seen X" row injected into AIS vessel popups (via `popupHtml`) and OpenSky
  aircraft popups (via `aircraftPopupHtml`) when the entity's identifier is
  present in the feed cache.
- `runProximityQuery()` gains an "Entity Feed Corroboration" third table listing
  vessels and aircraft inside the proximity radius that are independently
  confirmed in the entity feed, sorted by `observation_count` descending, capped
  at 20 rows.  Hit count is included in the proximity header summary line.

### Bug fixes

- Ports and Terminals sidebar badge: corrected from `premium tier` to
  `enterprise tier` (`frontend/index.html`).  Regression from v1.42.0 tier
  move; JS locking logic was correct, only the static HTML label was missed.

### Release model change

- Introduced three-track delivery model documented in
  `project-planning/FORWARD_ROADMAP.md`.  Track A = one debt item per release
  from a fixed ordered queue; Track B = one performance win; Track C = one-two
  user-visible features.  Tracks are independent — an unfinished item rolls
  alone without blocking other tracks.
- `project-planning/V1_44_TRIAGE.md` rewritten with developer-ready acceptance
  criteria for all three tracks.

### Header version display carry-forward resolved

- Carry-forward from v1.42.0 is closed.  `#hdrVersion` element is present in
  `index.html`, `loadVersion()` calls `/api/version` (not `/api/health`), and
  `api/routes/version.py` is registered and auth-exempt.  The display was
  functional after `15c627b`; the carry-forward note was written before that
  commit landed.  No further work required.

### Deferred to v1.44.0

- About and Legal pages alignment + `LEGAL.md` for public repo.
- Maintenance / backend-unavailable static page.
- Watchlist alert panel.

---

## v1.42.0 — 2026-04-05

### Ports and Terminals moved to enterprise tier; hypothesis expiry; intel route hardening

#### Tier change: Ports and Terminals (enterprise-only)

- `/api/static/ports` now requires enterprise tier. Previously premium.
- Rationale: dataset indexing load, proximity scan cost across the full
  bundle, and VIIRS AOI enrichment volume are disproportionate for
  non-enterprise deployments.
- The layer is renamed from `Ports` to `Ports and Terminals` throughout the
  frontend — display names, toggle controls, zoom notes, and popup subtitles.
  The API endpoint path and internal `featureId` are unchanged to avoid
  breaking existing deployments.
- Backend: `require_session_tier(request, "enterprise")` replaces the
  previous `"premium"` guard in `api/routes/static_layers.py`.
- Frontend: `isEnterpriseFeatureLocked("ports")` replaces the
  `isStarterPremiumOnlyFeatureLocked` call in `loadPorts()`.
  `ENTERPRISE_ONLY_FEATURES_DEFAULT` list added; `"ports"` removed from
  `STARTER_PREMIUM_ONLY_FEATURES_DEFAULT`.
- `PREMIUM_ONLY_TOGGLE_CONTROLS` entry for ports gains `requiredTier:
  "enterprise"`. `updatePremiumOnlyToggleControls()` now reads
  `requiredTier` from each control entry and generates the correct locked
  state and tooltip for both premium and enterprise thresholds.
- Toast messaging updated: locked sessions see "Ports and Terminals requires
  enterprise access" rather than the generic premium-locked copy.

#### Dashboard item expiry — hypothesis TTL

- `HYPOTHESIS_MAX_AGE_HOURS = 48` added to `core/store.py`.
- `EventStore.prune_old_hypotheses(max_age_hours)` added. Uses
  `timestamp` (falling back to `first_seen_utc`) as the age reference.
  Hypotheses with missing or unparseable timestamps are retained rather than
  dropped. Returns the count removed.
- `api/scheduler.py` calls `store.prune_old_hypotheses()` inside
  `_persist_shared_runtime_state()` on every collector cycle.
  This prevents the hypothesis deque accumulating stale entries across
  long-running deployments and keeps the analyst panel uncluttered.
- `GET /api/hypotheses` gains `max_age_hours` query parameter (1–8760).
  Passes through to `get_hypotheses()` as an on-request age filter
  independent of the scheduled prune.

#### Intel route hardening (carry-forward from uncommitted)

- `api/routes/intel.py`: `nav_warnings_table`, `broadcast_warnings_table`,
  and `recent_notams` now call `store.get_event_records()` instead of
  `store.get_events()` and access typed `EventRecord` fields directly.
  Removes the intermediate `.get()` dict-path pattern that silently
  returned `None` for missing keys rather than raising.
- `ET_SMAPS_AREA` import moved to module level in `intel.py`; previously
  deferred inside the route handler.
- `recent_notams` now uses `store.count_events()` for the total count
  instead of over-fetching 5000 records and slicing in Python.
  The redundant in-route `sorted()` calls are removed; ordering is now
  delegated to the store.
- `broadcast_warnings_table` secondary-sort comment updated to match
  current logic.

#### MIS persistent store — warning count cache

- `core/mis_persistent_store.py`: `warning_count()` now caches the line
  count keyed on `(path, mtime_ns, size)`. Repeated calls within a single
  scheduler cycle no longer re-open and scan the file. Thread-safe via a
  module-level `threading.Lock`.

#### Bench tool

- `tools/bench_health.py`: `X-Phantom-Frontend: dashboard-web` header
  added to benchmark requests so they are distinguishable from anonymous
  load in access logs.

#### Test coverage

- `tests/api/test_api.py`: space-weather test now inserts an older
  conditions record before the current one to verify the store correctly
  returns the newest Kp value rather than an arbitrary dict ordering.
- `tests/mis/test_mis_persistent_store.py` added (untracked).

#### Build tooling

- `Dockerfile`: `iproute2` and `strace` added to the runtime image to
  support the v1.42.0 hidden-cliff profiling pass described in
  `project-planning/V1_42_PROJECT_SPECIFIC_TRIAGE.md`.

---

## v1.41.1 — 2026-04-04

### Ports layer and thermal AOI triage

- Added a premium bundled global ports reference layer backed by
  `live_ais_ports.json`, including runtime fallback seeding from `bundled_data/`
  so the layer survives volume-backed startup seeding.
- VIIRS proximity alerts can now include ports as explicit AOIs instead of
  only energy, datacenter, and strategic-overlay context.
- VIIRS alert payloads now expose explicit thermal-triage fields for
  analyst-facing caution: `alert_class`, `alert_label`, `thermal_proxy_only`,
  and observation age metadata.
- The frontend now frames these hits as thermal AOI triage rather than direct
  explosion confirmation, shows age more clearly, and can reveal the matching
  premium port layer from the alert surface.

---

## v1.41.0 — 2026-04-04

### Truth surfaces and first replay scaffold

- MODU state now arrives normalized at ingest: the collector emits `status_bucket`,
  `status_detail`, and `active` so cluster logic and popups use server-side truth
  instead of repeatedly inferring state from raw NGA strings in the browser.
- VIIRS fire subtype fidelity is now explicit. When current fire granules arrive
  without usable subtype fields and collapse into generic `thermal_anomaly`
  output, collector health degrades visibly instead of silently implying the feed
  is dead.
- VIIRS layer counts now separate loaded, rendered, maritime-filter-held, and
  zoom-held state, which removes the recurring operator confusion where
  `Maritime thermals only` made a live feed look empty.
- Added `tools/replay_viirs_hotspots.py` and `core/replay.py` for deterministic
  offline hotspot-cluster replay against archived `events_snapshot.json` windows.
- Release planning for this line is now explicit in
  `project-planning/V1_41_RELEASE_CHECKLIST.md`, and release sync remains guarded
  by `tools/release_check.py`.

---

## v1.40.0 — 2026-04-04

### Mobile — first-class release

This release makes the dashboard genuinely usable on mobile for the first time. The
previous state had a white-screen regression on marker tap, an onboarding modal that
could become unreachable when the iOS keyboard appeared, and left-panel items sized
for touch but with no reduction in vertical density on desktop.

#### White screen on marker tap — fixed

Opening the detail drawer on mobile triggered the panel backdrop at
`rgba(255,255,255,0.96)` — effectively a white screen covering the map while the
right panel slid in. The backdrop is now a dark semi-transparent overlay
(`rgba(0,10,20,0.48)`) consistent with standard mobile drawer patterns. The map
is dimmed, not hidden.

The `backdrop-filter: blur(1px)` that accompanied it has also been removed: 1 px blur
is imperceptible at any normal display density and triggered a full GPU compositing
pass for no visible benefit.

#### API unavailable on mobile — fixed

New mobile users hit the onboarding email gate, which opens a dialog. The dialog used
`position: absolute` anchored to the layout viewport. On iOS Safari, the layout viewport
does not shrink when the software keyboard appears — the visual viewport does. This meant
the submit button was pushed behind the keyboard with no way to reach it. The gate
promise never resolved, every subsequent API call returned a transport failure, and the
header showed `API unavailable`.

Fixes applied:
- `position: absolute → fixed` on `.dialog-backdrop` so it tracks the visual viewport.
- `align-items: flex-start` on the backdrop so the dialog anchors at the top of the
  screen, above the keyboard, rather than centering across the full layout height.
- Mobile override `max-height: min(calc(100dvh - max(32px, calc(var(--safe-top) + var(--safe-bottom) + 32px))), 760px)` on `.dialog` so the form remains fully scrollable and safe-area insets on notched devices are respected.
- `overflow-y: auto` on the backdrop so the dialog is reachable even if it is taller
  than the available viewport.

The same `position: fixed` change also applies to the desktop case, where `overflow-y: auto`
combined with `align-items: center` was a latent bug: a dialog taller than the viewport
would have been clipped at the top with no scroll path to the beginning.

#### Access key input alignment — fixed

The sidebar inline access-key input was rendered at `font-size: 16px` despite the
compact form's intent of `12px`. The global `input:not([type="checkbox"])` rule
(placed later in the cascade and with matching specificity `0,2,1`) was silently
winning. The fix adds an `input` type qualifier to the override selector placed
after the global rule so cascade order and specificity together guarantee the
compact size. The input also now carries `width: 100%` explicitly to ensure it
fills its flex container in all browsers.

#### Left-panel desktop density

All interactive items in the left sidebar previously used 44 px minimum heights —
correct for touch targets on mobile, but causing substantial wasted vertical space on
desktop where pointer precision is available. The two `@media (min-width: 981px)`
blocks that governed access-panel and sidebar overrides have been merged, and desktop
now reduces:

- `layer-toggle-item` and `layer-subfilter-item`: 44 px → 30 px min-height
- `toggle-row`: 44 px → 28 px min-height, 8 px → 4 px top margin
- Toggle switch: 44×44 px → 38×28 px, with proportionally scaled track and thumb
- `tw-btn` (1H / 3H / 6H / 12H / 24H / ALL): 44 px → 26 px min-height
- `sb-section` padding: 12 px 14 px → 8 px 12 px
- `sb-title` margin-bottom: 10 px → 6 px

Mobile retains all 44 px touch targets unchanged.

#### CSS hygiene

- All five instances of `-webkit-overflow-scrolling: touch` removed. The property
  has been a no-op since iOS 13 (2019); momentum scrolling is on by default.
- `backdrop-filter: blur(1px)` removed from `.panel-backdrop` (see above).
- `viewport-fit=cover` added to the HTML `<meta name="viewport">` tag so the
  layout correctly accounts for safe-area insets on notched and Dynamic Island devices.
- Cancel button wired into the access-panel inline form HTML to match existing CSS
  selectors that already addressed it.

### [Unreleased] — v1.40.0 planning

### Next release direction

- **Replay and truth checks still gate the next expansion**: land at least one deterministic replay or backtest slice and one explicit post-deploy truth check for auth, intake, and critical startup sources before opening another data-growth lane.
- **Performance follow-through must be measured, not assumed**: rerun the heavy GeoJSON profiling path plus the protected browser-path probe on the shipped `v1.39.0` branch and keep both backend serialization cost and frontend refresh churn in scope until the profile proves the remaining budget is acceptable.
- **Operational recovery still outranks source sprawl**: Redis restart recovery, VIIRS retention discipline, and scheduler-storage-class regression coverage stay ahead of the next feed add.
- **The next datasource decision is now explicit**: triage MODIS Terra/Aqua active-fire coverage against existing VIIRS ingest for maritime contradiction value, duplicate semantics, latency, and offshore policy before any collector work starts.

### Frontend mobile QA and release discipline

- **iPhone-width regressions are now covered in automated WebKit checks**: Playwright mobile coverage now runs the dashboard and public pages at 375 px, 393 px, and 430 px widths with assertions for `viewport-fit=cover`, no horizontal overflow, 44 px touch targets, drawer behavior, and bottom-sheet containment.
- **The iOS Safari release checklist is now versioned in-repo**: `docs/iOS-Safari-QA.md` records the manual pass for notch-safe layout, tap targets, form zoom prevention, safe-area handling, and the exact mobile widths the release line must hold.
- **Static page scope is now explicit instead of assumed**: the repository audit found three customer-facing HTML entry points under `frontend/` and no additional static pages outside that tree, so the hardened safe-area treatment and regression suite now cover the whole current public surface.

## v1.39.0 — 2026-04-03

### Thermal triage and operator context

- **VIIRS maritime thermals are easier to isolate and interpret**: the dashboard now exposes a `Maritime thermals only` subfilter, uses scientific detection classes for marker treatment, and keeps `FP_type`, pixel footprint, and convergence context visible in the popup flow.
- **Offshore heat now carries live risk framing instead of raw dots only**: VIIRS detail surfaces now distinguish offshore and gas-flare-style detections more clearly, show when a hit overlaps a high-risk box, and keep the most relevant contributing signals visible at the point of inspection.
- **Thermal judgement is now explicit instead of implicit**: VIIRS fire detail and proximity surfaces now show a policy outcome of `BACKGROUND`, `CONTEXT`, `WATCH`, or `PAGE`, so operators can see whether the system is treating a hit as routine heat, context worth reading, something to watch, or a page-worthy anomaly.
- **Known offshore flare basins now act as negative controls**: routine hydrocarbon regions in the Gulf, Bahrain offshore, and Red Sea energy basins are now encoded as suppressors so ordinary flare signatures do not get promoted just because they sit inside a noisy strategic area.
- **MODIS is documented as a corroboration lane, not a hidden live source**: the shipped UI now explains MODIS' intended role in the thermal policy flow, but `v1.39.0` still treats it as a datasource decision and replay target rather than a peer alert feed.
- **Duplicate semantics are visible to the operator**: the thermal popup now explains the intended merge rule for cross-sensor and repeated thermal detections so persistence can be separated from duplicate noise during live triage.
- **Thermal policy now has its own assessment badge**: this is intentionally a judgement icon in the popup and banner flow, not a separate map-marker family, so source identity and policy outcome do not get conflated.

### Persistence truth and refresh discipline

- **ClickHouse storage health is visible end-to-end**: `/api/health` now exposes persistence state and pending buffered events, the frontend alert stack can surface degraded storage truth, and startup can fail closed when persistence is required.
- **Partial ClickHouse flush failures now requeue buffered events instead of silently dropping evidence**.
- **Steady-state browser work is lighter**: hidden layers stop refreshing by default, large event snapshots no longer rewrite `sessionStorage` every poll, and closed intel tables stop fetching in the background unless explicitly opened or forced.
- **Marker vocabulary is cleaner under load**: the map icon set now uses a wider SVG shape vocabulary so high-frequency layers no longer collapse into the same small handful of `pin`, `diamond`, and `star` markers.

### Operator tooling and regression hardening

- **Access-key management is no longer trapped behind flags only**: `tools/manage_api_keys.py` now supports an interactive default menu plus explicit permanent key removal alongside the scripted subcommands.
- **The local triage workflow is more concrete**: `make probe-local` and `tools/probe_local_stack.py` exercise the protected browser path directly.
- **Regression coverage followed the release cargo**: added persistence checks cover ClickHouse field-confidence round-trip plus batch requeue behavior, `ndbc_sar2` changed-file fetches now run concurrently under test, and dead-code / unreachable-path cleanup continued alongside the release cut.

## v1.38.1 — 2026-04-03

### Frontend UX tightening

- **The old manual refresh controls were redundant and are now removed**: the header `Refresh` and `Force Refresh` buttons are gone, the Intel tables `Reload` button is gone, and the UI now exposes the existing automatic refresh loop through a passive `Next refresh` countdown instead of duplicate operator controls.
- **The dormant sidebar search UI is removed for now**: the unused search bar, count badge, empty-state chrome, and the matching keyboard-shortcut copy were all still visible even though that surface is not part of the current workflow.
- **The colored access-tier banner can now be dismissed per session**: the banner no longer sticks on screen with no exit path once starter or premium state is resolved.
- **The premium depth rows now unlock correctly on premium-plus sessions**: `Expanded aircraft depth` and `Expanded sanctioned-fleet depth` were still behaving like starter-only legacy placeholders and did not become usable when the session tier upgraded.
- **Premium sessions can now intentionally drop back to preview depth**: once the expanded-depth rows are available, the operator can keep full depth on or explicitly fall back to the preview cap instead of being locked into the old one-state behavior.
- **Starter access actions now line up correctly**: the sidebar `Starter active` and `Enter API key` surfaces no longer sit out of alignment in the access panel.
- **Request-access copy is clickable everywhere it appears**: the raw access-request URL is replaced with actual links in the sidebar and auth dialog so the user can click straight through to the same request page.

## v1.38.0 — 2026-04-02

### Performance and serve-path hardening

- **Steady map polling now reuses work until data actually changes**: GeoJSON responses are cached against source revisions instead of a 25-second wall-clock TTL, so unchanged layers stop missing the cache on routine 30-second refreshes.
- **Sanctioned-vessel and zone paths shed avoidable allocation churn**: vessel routes now filter directly on source-specific `EventRecord` snapshots and TankerTrackers zone polygons rebuild their shapely index only when the zone source mutates.
- **Editable installs now keep the fast JSON path**: `orjson` is declared in `pyproject.toml`, which stops pyproject-driven environments from silently falling back to stdlib JSON on the largest response payloads.

### Access, onboarding, and operator truth

- **Starter onboarding now gates browser-session API access explicitly**: protected browser sessions require a server-issued onboarding cookie before the rest of the API unlocks, while `/api/auth/session` status remains readable so the frontend can recover cleanly.
- **Onboarding intake is stricter and more useful**: the backend rejects obvious placeholder addresses, enforces uniqueness for sign-up emails, and keeps auth, onboarding, and intake POST responses marked `no-store` so stale session state is not cached by the browser.
- **The map now has an optional locate-me flow with runtime-only logging**: a small Leaflet control centers the map on the browser's current location when the user asks for it, draws a lightweight accuracy overlay, and writes a runtime-only server-side location event for later operator review.

### Release and planning hygiene

- **April triage notes were folded back into the live planning surfaces**: the master plan now owns the carry-forward from the outage, performance, remote-runtime, and silent-failure passes, while the release diary records the consolidation and the redundant scratch notes are retired.
- **Release markers are aligned on `v1.38.0`**: runtime metadata, package version, internal README, and the public-doc sync pass now agree on the shipped line instead of leaving the onboarding and perf work stranded between planning and release state.

## v1.37.0 — 2026-04-02

### Thermal intelligence and operator context

- **VIIRS now behaves like an analyst surface instead of a raw feed dump**: the dashboard separates thermal fires from DNB night-light detections, exposes hotspot clusters with unusualness scoring, renders pixel-footprint geometry when available, and shows context-aware banners for both proximity alerts and unusual hotspot zones.
- **Thermal detections now carry more explainable nearby context**: hotspot and proximity routes surface nearby port, offshore, nuclear, datacenter, and military context so unusual heat near strategic infrastructure is easier to interpret without leaving the dashboard.
- **Dense thermal layers are more truthful about what is loaded versus what is visible**: zoom-aware VIIRS counts, disclosure hints, subfilter counts, and zoom-scaled markers now explain why the map is or is not rendering a given thermal slice.

### Performance and startup hardening

- **The main VIIRS proximity bottleneck was removed at the root cause**: the hot route now works from raw `EventRecord` access paths instead of recursively materializing full dict payloads, which removes the earlier serialization cliff under repeat load.
- **Heavy static reference layers no longer drag first render into a startup burst**: large maritime and reference payloads are cached server-side, and saved premium toggles now restore after first paint through an idle staggered queue instead of fan-out loading during auth bootstrap.
- **Python 3.14 triage is now the default local debugging path**: runtime debugging hooks, container helpers, and test coverage now support faulthandler dumps, live `pdb -p` attach, and reproducible `cProfile` slices without relying on `py-spy` as the default workflow.

### Persistence and operator truth

- **Geometry-bearing evidence no longer falls out of persistence silently**: ClickHouse inserts now serialize event geometry correctly and restore it on read, closing the earlier silent geometry-loss path for VIIRS and other geometric evidence.
- **Source health is harder to miss during degraded runs**: the dashboard now auto-expands health state when sources are degraded, stale, or cache-backed unless the operator explicitly collapses it.
- **Release markers are aligned on the shipped line again**: internal metadata, launcher output, runtime release info, and both repos' release surfaces now agree on `v1.37.0` as the current release.

## v1.36.0 — 2026-04-02

### Starter access and session upgrades

- **Starter now cleanly upgrades through exchanged browser sessions**: local and public optional-auth deployments start anonymous users on `starter`, then upgrade features when a valid key is entered through the header or sidebar auth UI.
- **Freshly created keys now validate against the live Docker app**: the host-side access-key store is mounted into `/app/data/auth`, so `tools/manage_api_keys.py` and the running container no longer drift onto different auth stores.
- **The access UI is less confusing on mobile and desktop**: the header now surfaces an explicit `Enter API key` entry point, the sidebar no longer duplicates the unauthenticated upgrade CTA, and the Sea State legend now has a smaller clean dismiss control.

### Source, rule, and API hardening

- **Collector and route normalization work shipped across the current dirty line**: AIS, DailyMem, GUIDE, MIS, NDBC, NOTAM, VIIRS, SWPC, USGS, raw events, vessel routes, and intel paths all carried forward the current parsing, threshold, and response-shape fixes already accumulated in the tree.
- **Core scoring and policy paths were tightened together**: convergence, access policy, collector base behavior, ClickHouse write-through, callsign/reference lookups, and maritime/rule logic now reflect the current branch state instead of leaving those fixes stranded outside a release.
- **Regression coverage moved with the runtime changes**: focused tests for API access, AIS, ICC, MARAD, and geometry behavior ship with the current line rather than sitting unversioned beside it.

### Tooling and release hygiene

- **Local key-management guidance now matches the working runtime**: API auth notes, README guidance, and key-management tool copy now distinguish starter/premium/enterprise user upgrades from the private `operator` tier.
- **Release markers are back in sync**: package metadata, runtime release metadata, launcher banner text, internal instructions, and both repos' release surfaces now agree on `v1.36.0` as the shipped line.

## v1.35.0 — 2026-04-02

### Access gate and runtime-only intake

- **Starter access now has a real first-use gate**: the browser blocks on a low-friction email modal before the starter dashboard starts, rather than treating onboarding as a cosmetic overlay after the app is already running.
- **Email submissions now stay on-box in runtime-only storage**: the backend validates and appends normalized email entries into a JSONL intake log under `data/intake/`, with a server-generated UUID directory, restrictive file permissions, and no public route exposure.
- **Protected-access UX now aligns better with anonymous starter**: optional-mode deployments now describe starter access as anonymous by default while keeping the API-key upgrade path explicit for expanded features.

### Release hardening and planning discipline

- **Starter-tier limits now hold across both map and raw event APIs**: the raw `/api/events` route now applies the same starter cap discipline as `/api/events/geojson`, closing an easy path around the lighter public view.
- **Runtime auth and intake stores are kept out of git again**: `data/auth/` and `data/intake/` are now ignored so server-side state does not leak into release staging by accident.
- **The next datasource line is more explicit and less novelty-driven**: the release planning corpus now ranks AviationWeather.gov first, FAA registry second as reference enrichment, and AVWX as hold-only until an official-source gap actually exists.

## v1.34.0 — 2026-04-02

### Production sync and access truth

- **Frontend access state now follows server truth on downgrade**: session expiry, logout, or tier downgrade now clears stale live state instead of leaving privileged or higher-tier data rendered after the backend has already narrowed access.
- **Optional auth no longer behaves like enforced auth after logout**: deployments using `PHANTOM_AUTH_MODE=optional` now fall back cleanly to starter access and keep the refresh loop alive instead of freezing the dashboard as if all API access were revoked.
- **Protected-session UX is more explicit**: the browser now shows a visible access panel with current tier, session status, and expiry, and the unlock flow is tested against both raw `pt_live_...` tokens and full CLI output lines.

### Performance and collector hardening

- **GeoJSON hot-path work is now directly reduced on the response side**: cache hits reuse pre-serialized JSON bytes, and capped map responses keep newest-first semantics without sorting the entire filtered result set before slicing.
- **Slow UI and slow API complaints can now be correlated instead of guessed**: backend request IDs and `Server-Timing` headers now align with the browser perf ledger behind `?debug_perf=1` for repeatable triage.
- **Two production-facing soft-failure paths were tightened**: repeated AIS upstream reader failures are log-throttled instead of flooding normal runtime, and TankerTrackers sanctions now accepts the current dict-wrapped upstream payload shape instead of silently flattening to zero events.

### Analyst-visible truthfulness

- **NDBC DART is now a first-class visible layer**: the DART anomaly feed is exposed in operator controls instead of being wired only in frontend internals.
- **NOTAM and VIIRS geometry is more explicit on the map**: NOTAM circle overlays render from canonical backend event geometry, and VIIRS proximity alerts now return and render their search radius directly.
- **MODU field-state summaries preserve more real state**: cluster and popup summaries now keep mixed non-active regional context instead of collapsing every non-active rig into a generic removed bucket.

## v1.33.0 — 2026-04-01

### Outage containment and runtime hardening

- **The GeoJSON CPU outage is fixed at the real hot path**: bulk `/api/events/geojson` responses no longer force maritime enrichment by default, the handler no longer blocks the event loop thread, and maritime index rebuilds are keyed to file signatures instead of a five-minute TTL.
- **Maritime reference caching is now stable under repeat load**: gzipped layer payloads are cached per file version, first-build index work is serialized inside a process, and very large feature sets skip analyst-facing enrichment instead of turning the default map feed into a CPU trap.
- **Frontend failure handling is less silent**: the browser now surfaces API-unavailable states explicitly, avoids follow-on refresh work when the backend is down, and keeps the header state honest instead of looking healthy while requests fail.

### Release discipline and operational evidence

- **Release markers are boxed off on `v1.33.0`**: runtime metadata, package versions, launcher output, internal docs, and public docs now agree on the shipped bug-fix line instead of leaving the outage work stranded in `v1.33.0` planning.
- **The outage record is now publishable instead of tribal knowledge**: the full internal RCA and triage remain in `project-planning/`, and public-safe incident notes are mirrored into the sibling `../phantomtide` docs repo like the earlier OOM postmortem.
- **Local containers now include `py-spy` for live profiling**: the app image installs `py-spy`, and local Docker compose grants the ptrace permissions needed to sample hot Python workers during future silent failures or slow-path triage.

## v1.32.0 — 2026-04-01

### Intelligence and analyst UX

- **VIIRS proximity alerting is trustworthy again**: close-range offshore and gas-flare detections near strategic context are promoted back into the analyst-facing alert path, while routine datacenter-adjacent heat stays suppressed.
- **Maritime context no longer shows analyst-useless global cable distances**: `nearest_cable_km` is omitted when the nearest submarine cable is more than 1000 km away, preventing misleading four-digit distance readouts from crowding non-maritime detail panels.
- **Starter-tier preview UX is less literal and more usable**: starter messaging is now generic instead of source-name heavy, the alert banner no longer exposes per-layer cap summaries, limited preview layers render in a visibly greyed state, and the locked-depth controls now frame the upgrade path around expanded access rather than provider-specific wording.
- **Protected-access surfaces are clearer in the browser**: the header `Access` entry point, dialog labels, and session copy now use `access key` wording and align with the public access-request path.

### Release hygiene and documentation

- **Access-control docs now draw a hard line between anonymous and operator access**: open local dev stays `operator` by default for full-feature testing, while public anonymous access is documented as `starter` tier when `PHANTOM_AUTH_MODE=optional` is used.
- **Env and dead-code drift were cleaned up for the release line**: `.env.example` now mirrors the runtime keys the code actually reads, the local `.env` non-secret keys were aligned to that shape, and the Vulture audit is clean after whitelisting FastAPI/app entrypoints plus removing the orphaned `NDBC_DART_DIR_URL` constant.
- **Access request handling is routed through the public repo instead of named personal contact copy**: starter-limit support text, the public README, and the access-policy payload now point users to a dedicated GitHub access-request flow for higher-tier API keys.
- **Release metadata now matches the shipped line again**: internal package versions, runtime release metadata, public docs markers, and roadmap notes all align on `v1.32.0` as the current release and `v1.33.0` as the next planning line.

## v1.31.0 — 2026-04-01

### Access control and product discipline

- **Optional dashboard auth landed as a deployment-wide session gate**: protected deployments now reject `/api/*`, `/docs`, `/redoc`, and `/openapi.json` until the browser exchanges an opaque operator key for a short-lived `HttpOnly` session cookie, while open local development can still stay off by env flag.
- **Operator key lifecycle is now explicit and scriptable**: `core/auth.py` provides hashed API-key storage plus signed session helpers, and `tools/manage_api_keys.py` handles secret generation, key creation, listing, and disable flows against `data/auth/api_keys.json`.
- **Starter-tier exposure is now intentionally sparse**: the default map profile is reduced to AIS plus navigation warnings, dense premium-candidate layers stay off by default, and OpenSky plus sanctioned-fleet map depth is capped to 10 markers each until a fuller tier model is shipped.
- **Military-installation data is now internal-only**: the user-facing route and frontend load path were removed, VIIRS proximity results no longer disclose military nodes, and the remaining sidebar toggle behaves as an enterprise placeholder instead of a dead control.

### Source truthfulness and collector hardening

- **Collector health states now preserve backend run modes end-to-end**: `down` runs no longer collapse into a generic `failed` label, so the UI can distinguish `empty`, `error`, `cache`, `stale`, and `partial` honestly.
- **NERACOOS now reports mixed freshness truthfully**: station-level fetch failures surface in health detail, `UCONN_WLIS_MET` joins the monitored set, and mixed fresh/stale observation sets now resolve to `partial` instead of flattening the whole source into stale-or-live.
- **DART live polling was restored against NOAA's current products**: the collector now reads `realtime2/*.dart` and `5day2/*_5day.dart` instead of the dead legacy layout, uses a curated active-station roster, and surfaces per-station read failures directly in source health.
- **NOTAM now ingests directly from FAA SWIM JMS**: the collector drops the REST sidecar path, drains the direct JMS buffer when credentials exist, and falls back only to the local cache when no live JMS source is available.

### Runtime and release hygiene

- **Runtime roles now support split API and worker deployments**: `core/runtime_roles.py` makes scheduler ownership and proxy discovery follow `PHANTOM_RUNTIME_ROLE`, with env overrides for explicit control.
- **Access-control docs and env examples now match the shipped behavior**: `.env.example`, the internal README, and `project-planning/API_AUTH.md` now document the auth configuration and operator workflow coherently.
- **Release metadata drift was corrected**: internal package versions, frontend package metadata, `release.json`, roadmap docs, and changelog markers now agree on the shipped `v1.31.0` line and the active `v1.32.0` planning line.

### Collector health and UI truthfulness

- **Collector health states now preserve backend run modes end-to-end**: `down` runs no longer get flattened to a generic `failed` mode in `SourceHealth`, so the UI can distinguish `empty`, `error`, `cache`, `stale`, and `partial` instead of collapsing them into ambiguous badges.
- **NERACOOS no longer degrades opaquely**: stale upstream observations still surface as stale, but station-level HTTP/fetch failures now show up in health detail and total live-fetch failure is recorded as an explicit down/error state.
- **DART no longer fails silently behind `0 stations polled`**: directory discovery, station-coordinate refresh, and per-station read failures now feed health detail directly, and the current NDBC station-table LOCATION format is parsed correctly instead of assuming obsolete numeric lat/lon columns.

## v1.30.0 — 2026-04-01

### Release direction

- **Rebuild from the shipped baseline completed**: `v1.29.0` remained rolled back, and `v1.30.0` was cut from the real shipped `v1.28.0` baseline instead of the abandoned candidate line.
- **Evidence fidelity outranks surface expansion**: archive-vs-cache separation, replay/backtest scaffolding, and trustworthy release sync are the real next release, not another feed grab.
- **First archive boundary landed**: the USGS collector now archives its raw GeoJSON feed under runtime data before normalization, and cached EventRecords now preserve provenance metadata instead of dropping it on reload.
- **Release metadata now has a canonical runtime source**: the dashboard header version reads from `release.json` through `/api/health`, so the shipped release line no longer depends on hardcoded frontend text.

### Mobile

- **Compact-screen detail panel no longer gets covered by sea-state legend**: when the mobile detail drawer is open, the bottom-right weather legend now yields instead of sitting underneath vessel attributes.

### Labels / data quality

- **Stale `_WATCHLIST_CATEGORY_DISPLAY` remap in `api/routes/intel.py`**: all 24 remap keys (e.g. "Toy Soldiers") are absent from the current `plane_alert_db.json`; the DB already ships clean English category names. The dict and `_display_category()` can be removed entirely once confirmed no live Redis/CH rows carry the old informal keys.
- **`reports/labels_review.csv`** (2263 rows, untracked): full label audit covering 50 aircraft categories, 2155 aircraft tags, 24 stale remap entries, 2 vessel watchlist sources, 32 event types. Needs analyst review; import tooling to follow (hide/rename/delete actions per row).
- **Label cleanup required**: aircraft tags contain meme language, jokes, attitude, filler, typos, and vibe descriptors. Professional dashboard needs denotative labels, not performative. Worst offenders identified for removal/replacement: childish/jokey tags (e.g., "Aaaaaaaand It's Gone", "AbsoluteRuler4Life", "Get To The Choppa"), vague/flippant tags (e.g., "Advanced", "Actor", "Soft Drinks"), and sloppy semantics (duplicates, typos, internal shorthand). Rule set: no jokes, memes, slang, attitude, rhetorical questions, opinionated descriptors, internal shorthand, duplicate semantics, or insider-context labels.

### Source triage

- **Datasource scratchpad moved out of the changelog**: the long-form ArcGIS and endpoint research notes now belong in `project-planning/EXTERNAL_ARCGIS_SOURCES.md` and the master plan backlog, not in release notes.
- **Hong Kong Marine Department arrivals / departures promoted to backlog triage**: validate machine-readable access, identifier quality, timezone handling, and whether port-call events materially improve AIS contradiction detection around Hong Kong approaches.
- **NWS API and NWS_Mapping promoted to backlog triage**: probe marine/coastal alert geometry, update cadence, and overlap risk against ECCC, NDBC, and existing weather layers before any collector work starts.
- **NOAA coastal ArcGIS estate sweep formalized as discovery work**: enumerate `Hosted`, `MarineCadastre`, `OceanReports`, and `NWS_Mapping`, then only promote layers that add control, infrastructure, or restriction context rather than decorative overlays.
- **Public docs inventory is now capability-level, not feed-by-feed**: public release material keeps `AIS (limited)` visible but otherwise describes the live platform in functional terms instead of publishing the full operational source map.

### Triage queue

- **v1.30 priority order is now explicit**: fix trust-breaking bugs first, then real performance bottlenecks, then evidence-fidelity features, then only selective source promotion.
- **Trust-breaking bug queue leads the release**: nearest-cable accuracy, OpenSky restart validation, snapshot repopulation proof, and stale watchlist-display logic cleanup all outrank new collectors.
- **Real performance work is now called out separately from feature growth**: convergence recomputation on every request and the 30-second frontend poll fan-out are now treated as first-class release debt.

### Performance / fidelity

- **Convergence snapshots now use a short-lived response cache**: `/api/convergence` now reuses a 20-second cached payload when the request shape and in-memory store fingerprint have not changed, which removes redundant recomputation from the default dashboard poll loop.
- **Frontend refresh fan-out is now split by cadence**: slow-moving sources and slower overlays no longer refetch on every 30-second cycle, and the intel tables panel now deduplicates in-flight fetches while still forcing a refresh when the analyst explicitly opens or reloads it.
- **Raw archival expanded beyond USGS**: the ICC collector now archives its live maps, categories, and markers payloads before normalization and attaches those archive paths to event provenance for replay/debug work.
- **Dead-code noise reduced in the v1.30 branch**: FastAPI-decorated static-layer routes are now whitelisted for Vulture, an orphaned MIS Playwright fallback was removed, and `core/json_utils.py` no longer carries unused locals.


### Maritime context

- **Nearest cable distance hardened around the anti-meridian**: `core/maritime_context.py` now wraps longitude deltas and nearest-candidate lookups across the date line before computing `nearest_cable_km`, with focused regression coverage for anti-meridian cases.

---

## v1.29.0 — rolled back candidate

This release candidate was not promoted.

- Treat `v1.28.0` as the last shipped internal/public release baseline.
- Rebuild the evidence-fidelity track as `v1.30.0` with honest release markers and replay-first validation.

## v1.28.0 — 2026-03-30

Maritime context completion, runtime data persistence hardening, and release sync.

### Maritime context completion

- `scripts/fetch_maritime_layers.py` now fetches NOAA MarineTransportation
  lanes/channels and ISA exploration areas, and the normalized outputs are now
  bundled under `data/_additional/`.
- `api/routes/static_layers.py` now serves `GET /api/static/marine-transport`
  and `GET /api/static/exploration-areas` alongside the earlier cable,
  routing, and EEZ overlays.
- `core/maritime_context.py` now enriches event GeoJSON with derived maritime
  context including `inside_eez`, `eez_name`, `nearest_cable_km`, `in_lane`,
  `marine_transport_name`, `routing_control`, `inside_exploration_area`, and
  `exploration_area_name`.
- The frontend now lazy-loads and renders marine transport and exploration
  layers, and detail surfaces expose the new maritime-context fields.
- Heavy static maritime overlays now use viewport culling on the frontend so
  wide-area map views stay responsive when multiple reference layers are
  enabled together.

### Runtime data persistence hardening

- `core/runtime_data.py` now defines the persistent runtime-data path used to
  seed bundled assets into the authoritative `/app/data` volume without
  overwriting live state.
- `core/local_cache.py`, `collectors/opensky/opensky_cache.py`, and
  `api/scheduler.py` now write the event snapshot, OpenSky cache, and MODU
  history through the runtime-data path instead of repo-local `data/`
  assumptions.
- Added focused regression tests for runtime-data sync, event snapshot
  persistence, OpenSky cache persistence, MODU history persistence, maritime
  layer fetch fixtures, and maritime context enrichment.

### Planning and release hygiene

- Retired planning docs are now consolidated into
  `project-planning/PHANTOM_TIDE_MASTER_PLAN.txt` with
  `project-planning/ROADMAP_HISTORY.txt` and
  `project-planning/RELEASE_DIARY.txt` preserving historical context.
- `TAGS_REVIEW.csv` moved to the repo root to match the existing aircraft-tag
  tooling expectations.
- Internal and public release markers are now synced to `v1.28.0`.

## v1.27.0 — 2026-03-30

Structured squawk taxonomy, maritime reference layers, and reliability fixes.

### Structured squawk taxonomy

- `core/callsign_db.py` now classifies squawk rows as `emergency`,
  `special_use`, `allocation`, `routing`, `monitoring`, `conspicuity`,
  `operational`, `administrative`, or `ambiguous` instead of treating the
  bundled UK squawk table as plain description text.
- OpenSky ingest now stores typed squawk context (`squawk_kind`,
  `squawk_actionable`, `squawk_inference_applicable`, `squawk_jurisdiction`,
  `squawk_source`, `squawk_ambiguous`) so downstream UI logic no longer has to
  infer mission meaning from free-text labels.
- UK-only squawk meanings are now geographically gated to a conservative UK
  airspace envelope before they appear in aircraft detail or drive SAR /
  mission inference. ICAO emergency codes remain globally applicable.
- Administrative allocations such as `Assigned by CCAMS`, ORCAM transit blocks,
  conspicuity codes, and frequency-monitoring codes no longer produce
  `Mission Operator` or `SQUAWK CONTEXT` badges by themselves.

### Maritime reference layers

- Added `scripts/fetch_maritime_layers.py`, a reusable ArcGIS FeatureServer
  paginator and GeoServer WFS fetcher that writes normalized GeoJSON to
  `data/_additional/` using the internal contract
  `{ source, layer_type, geometry, properties }`.
- Added static API routes for `GET /api/static/submarine-cables`,
  `GET /api/static/vessel-routing`, and `GET /api/static/maritime-regions`.
  Each route returns an empty `FeatureCollection` until its backing data file
  has been fetched.
- The frontend now exposes lazy-loaded reference toggles for NOAA submarine
  cables, NOAA vessel routing measures, and MarineRegions EEZ boundaries.
  These layers provide jurisdiction and infrastructure context without adding
  a live collector.

### Reliability fixes

- `core/ch_store.run_migrations()` now applies `ADD COLUMN IF NOT EXISTS`
  startup migrations for the six columns introduced in v1.17.1 and is called
  from the FastAPI lifespan before `_hydrate_store()`. This fixes failed
  periodic ClickHouse flushes on older volumes that never replayed
  `01_schema.sql`.
- `infra/init/clickhouse/02_migrate_v1171.sql` adds the same migration as a
  manual recovery path for existing deployments.
- `collectors/ais/ais_collector.py` now uses exponential reconnect backoff
  (`3 * 2^(n-1)` seconds, capped at 120 seconds) after consecutive feed
  failures, reducing repeated warning floods against unavailable AIS sources.

## v1.26.0 — 2026-03-29

v1.26 release sync: NOTAM airport-centred jump parity, aircraft-label cleanup,
and public documentation refresh.

### NOTAM airport-centred map jumps

- Added `core/airport_lookup.py` to resolve airport coordinates from bundled
  `airports.json` aliases (`icao`, `iata`, `ident`, `gps_code`, `local_code`).
- `collectors/notam/notam_collector.py` now resolves three-letter and ICAO-style
  location designators through the shared lookup before falling back to FIR
  approximations.
- `api/routes/intel.py` now backfills `latitude` / `longitude` for recent and
  critical NOTAM intel rows from the NOTAM `location` field when the stored
  event has no renderable coordinates, so row click-through can zoom the map to
  the airport instead of failing silently.

### Aircraft watchlist label cleanup

- Added `core/aircraft_watchlist_labels.py` and applied it in both
  `core/watchlist.py` and `api/routes/static_layers.py` so stale runtime data
  no longer leaks junk aircraft tags such as `Aaaaaaaand Its Gone`,
  `Bunch Of Bankers`, and `Scrooge Mcduck` into the UI.
- `TAGS_REVIEW.csv` updated so future `planes_master.json` rebuilds no longer
  preserve `Scrooge Mcduck` as a deliberate self-mapping.

### Release and documentation sync

- Synced internal/public README and CHANGELOG files, roadmap state, FastAPI
  app version, and frontend fallback version label to `v1.26.0`.
- Refreshed the public README screenshot set in `../phantomtide/docs/screenshots/`
  to reflect the current UI and release metadata.
- Documentation now states that the full app checkout/runtime already bundles
  the airport reference JSON used for NOTAM jumps, and acknowledges
  `mwgg/Airports` plus alexander-san in the public-facing project material.

---

## v1.25.0 — 2026-03-29

v1.25 debt clearance sprint: cache I/O consolidation, AIS test coverage,
confidence model documentation, VIIRS facility cache silent-failure fix,
proxybroker package clarification, and timestamp audit.

### core/cache_io.py — TAX 7 resolved

- Extracted `load_event_cache(path, *, source_tag, filter_expired)` and
  `save_event_cache(path, events, *, source_tag)` into a new shared module.
  Eleven collectors previously each implemented identical `_load_cache()` /
  `_save_cache()` functions with minor per-collector variations. All eleven
  now delegate to the canonical implementation:
  eccc, ndbc_dart, neracoos, guide, icc, marad, fleetleaks, rss/gps_advisory,
  tankertrackers_lostandfound, tankertrackers_zones, usgs.
- `save_event_cache` writes atomically via a temp-file rename so a crash
  mid-write never produces a half-written cache file.
- `filter_expired=True` (MARAD) discards entries whose `valid_until` is past
  at load time; previously only MARAD implemented this correctly.

### AIS test coverage

- Added `tests/ais/test_ais_collector.py` with 64 offline unit tests covering:
  NMEA checksum validation, payload character decoding, bit conversion,
  AIS text decoding, geo-value range validation, scalar field decoders
  (SOG, COG, heading, draught, altitude, ROT), auxiliary MMSI detection,
  EventRecord construction from raw position data, coordinate rejection
  (out-of-range, AIS sentinel 91/181), timestamp reconstruction from
  `ais_ts_sec`, and NMEA sentence parse path (sentence → queue).

### Confidence model documentation

- Added canonical four-metric hierarchy to `core/constants.py`:
  `source_confidence` (source trust weight), `quality_score` (per-event
  data quality annotation), `hypothesis.confidence` (analyst-facing
  probability estimate), `convergence.score` (unbounded evidence weight).
  Documents that these cannot be collapsed into each other and defines
  the intended role for each in analyst-facing output.

### VIIRS facility cache silent-failure fix

- `api/routes/intel.py` `_load_viirs_facilities()`: replaced four bare
  `except Exception: pass` blocks with `logger.error(...)` calls so
  infrastructure dataset load failures are visible in logs. VIIRS proximity
  alert system was previously silently returning empty results when any of
  nuclear plants, datacenters, military bases, or strategic overlay files
  failed to load.

### proxybroker package clarification

- `requirements.txt`, `core/proxy_broker.py`, `tools/find_opensky_proxies.py`:
  clarified that `proxybroker2` is the Python 3.12+ compatible fork of the
  official `constverum/ProxyBroker` (`proxybroker==0.3.2`). The original
  targets Python 3.5–3.7 and fails on Python 3.10+. `core/proxy_broker.py`
  `_import_proxybroker_module()` already tries `proxybroker` (official) first
  and falls back to `proxybroker2`; `tools/find_opensky_proxies.py` updated
  to use the same dual-try pattern instead of hardcoding `proxybroker2`.

### Timestamp audit

- Full sweep of all collectors confirms timestamp semantics are correct:
  all collectors use upstream observation time as `EventRecord.timestamp` and
  fall back to collection time only when the upstream source provides no
  timestamp field (acceptable per CLAUDE.md convention). No violations found.

### Roadmap

- Added full debt audit findings (2026-03-29) to the CODE SMELL section
  with new items: DEAD BATTERY 1 (AIS test void), DEAD BATTERY 2 (VIIRS
  silent failure), SMELL 1 (confidence model hierarchy), SMELL 2 (timestamp
  semantics), SMELL 3 (proxybroker2 alpha), and ROADMAP DRIFT note.
- v1.25 task list updated to reflect all items resolved or carried forward.
- NOTAM parser backlog triage: evaluate `avwx-engine` as a lighter-weight
  parser base or fork for the NOTAM path, validate coverage against current
  Phantom Tide fields, and decide whether that can retire the current spaCy
  dependency from this slice without losing required cleanup hooks.

---

## v1.24.0 — 2026-03-29

v1.24 triage queue: OpenSky resilience fix, hypothesis anchor parity, MODU status
semantics, NOTAM FIR coverage expansion, and proxy tooling.

- **Target-aware proxy pre-warming** — `ProxyPool.get_target_winners(target_domain)`
  added. The OpenSky collector now merges env-configured preferred URLs with
  dynamically learned winners for `opensky-network.org` from the working cache,
  so proven proxies carry across restarts without requiring explicit env var
  re-configuration.
- **Proxy discovery tool** — added `tools/find_opensky_proxies.py`. Fetches
  proxy candidates from proxyscrape and geonode, tests each against the
  OpenSky authenticated endpoint, and writes confirmed working entries to
  `data/proxy_working_cache.json`. Supports `--limit`, `--keep`, `--timeout`,
  `--workers`, and `--dry-run` flags. Documents that OpenSky blocks public
  datacenter proxy IP ranges; the tool is designed for use with paid residential
  or rotating proxies supplied via `PROXY_POOL_URLS`.

### Hypothesis anchor parity

- **`HypothesisRecord` representative geometry** — added `representative_lat` and
  `representative_lon` fields. The rule engine now computes a centroid (`_centroid()`)
  from evidence events at hypothesis creation time and stores it on the record so the
  jump affordance survives evidence event ageing out of the in-memory deque.
- **Jump chip always available** — the hypothesis table now shows the `⊕` jump chip
  when either live evidence events exist in the current index OR representative coords
  exist on the hypothesis. Previously the chip disappeared as soon as evidence events
  aged out.
- **`_findHypothesisJumpTarget()` fallback** — function now falls back to
  `representative_lat`/`representative_lon` when no live evidence events are found
  in the current event index.
- All seven `HypothesisRecord.create()` call sites in `core/rules.py` updated to pass
  representative geometry.

### MODU cluster status semantics

- **Expanded inactive-status detection** — the `_removedRe = /removed/i` pattern in
  the map renderer now covers `STACKED`, `COLD STACKED`, and `INACTIVE` alongside
  `REMOVED`. These NGA MODU status values all indicate a platform is not actively
  drilling and should be classified as non-active for field cluster counts and
  marker styling. The cluster popup active/removed ratio now reflects NGA's actual
  status vocabulary rather than only the REMOVED case.

### NOTAM airport fallback parity

- **`_FIR_AIRPORT_MAP` expanded** — 47 → 140 entries. Added coverage for the Middle
  East and Southwest Asia (Baghdad, Damascus, Beirut, Kuwait, Jeddah, Emirates,
  Tehran, Karachi), South Asia (Delhi, Mumbai, Colombo, Male), Southeast Asia
  (Bangkok, Ho Chi Minh, Kuala Lumpur, Singapore, Manila, Jakarta, Phnom Penh,
  Vientiane), Northeast Asia (Incheon, Beijing, Kunming, Urumqi), North Africa
  (Tunis, Algiers, Casablanca, Tripoli), Sub-Saharan Africa (Nairobi, Johannesburg,
  Kinshasa, Niamey, Lagos, Abidjan, Dakar, Brazzaville, Antananarivo), South America
  (Brasilia, Buenos Aires, Santiago, Lima, Guayaquil, Paramaribo, Caracas, Trinidad),
  Canada (Gander Oceanic, Toronto, Edmonton, Vancouver, Montreal), Caribbean/Central
  America (Curacao, Tegucigalpa, Mexico City, San Juan), and Pacific (Tahiti, Nadi,
  Port Moresby, Honiara). NOTAMs from these regions now receive approximate map
  coordinates instead of landing in the no-coords fallback.

---

## v1.23.0 — 2026-03-28

Callsign and squawk enrichment for aircraft, mission-aware convergence, and release hygiene cleanup.

### Aircraft enrichment

- **Callsign and squawk enrichment database** — added `core/callsign_db.py`, loading
  `phantom_tide_callsign_lookup_compact.json` and
  `phantom_tide_additional_entities.json` at import time. Provides exact/stem
  callsign matching, UK squawk description lookup, SAR squawk detection, and
  additional mission/entity profiles for frontend and collector use.
- **OpenSky ingest enrichment** — `collectors/opensky/opensky_collector.py` now writes
  callsign roles, units, countries, platforms, confidence tier, conflict flag,
  loiter-suppression hint, squawk description, and SAR status directly into
  aircraft event attributes at ingest time.
- **Static aircraft enrichment endpoints** — `api/routes/static_layers.py` now serves
  `GET /api/static/callsign-lookup`, `GET /api/static/squawk-lookup`, and
  `GET /api/static/aircraft-entities` for frontend cache warm-up and analyst inspection.
- **Aircraft popup/detail enrichment** — the frontend now preloads callsign, squawk,
  entity, and fuel-burn reference data on startup. OpenSky detail now shows mission
  badges, "why interesting" context, callsign conflict warnings, SAR chips, squawk
  meaning, and a privacy footnote for aircraft with no static match.

### Convergence and rule quality

- **Mission-aware aircraft contributors** — convergence scoring now distinguishes
  SAR-active aircraft, naval loiter, and surveillance loiter from generic aircraft
  loiter. Contested callsign matches do not upgrade score weight.
- **False-positive suppression** — known survey / weather-recon / flight-inspection
  callsign families can now suppress generic aircraft loiter contributors to reduce
  obvious analyst-noise cases.

### Release hygiene and documentation

- **Bug triage narrowed and documented** — the three open UX/reliability issues were
  re-scoped in roadmap/notes form:
  OpenSky proxy persistence remains a real backend reliability problem;
  hypothesis click-through already works for intel-table rows but not every surface;
  recent NOTAM click-through already works when coordinates exist, with remaining work
  focused on airport/FIR fallback coverage.
- **Airport data attribution** — added UI and documentation credit for
  [`mwgg/Airports`](https://github.com/mwgg/Airports), whose `airports.json`
  dataset is used for NOTAM airport fallback coordinates.
- **Release metadata sync** — internal/public README versions and the dashboard header
  version label were updated to match the shipped release.

## v1.22.0 — 2026-03-28

Three new intelligence layers, CelesTrak GPS enrichment, and code cleanup.

### New sources

- **NDBC DART anomaly detection** — `collectors/ndbc/ndbc_dart_collector.py`. Polls up to 50
  deep-ocean DART buoys every 15 minutes. Computes a 24-hour rolling baseline per station and
  fires an `ET_NDBC_DART_ANOMALY` event when the current water-column height deviates > 3σ.
  Station coordinates resolved from NDBC `station_table.txt` with fallback to a hardcoded list
  of ~35 globally deployed IDs. Convergence weight 1.5 (3–5σ) or 2.5 (≥5σ), 6-hour lookback.
  Map layer: teal diamond markers scaled by sigma (12/16/22 px). REF_SOURCE; 15-min atomic replace.
- **CelesTrak GPS TLE enrichment** — `collectors/celestrak/celestrak_gps.py`. Not a map layer.
  Module-level TLE cache refreshed every 6 hours using the CelesTrak JSON feed. SGP4 orbital
  propagation + IAU 1982 GMST converts TEME→ECEF→local ENU to compute elevation angles.
  GUIDE GPS disruption events annotated with `visible_gps_count` and `expected_visible_count` at
  ingest time. Distinguishes jamming (all visible birds affected) from ionospheric interference
  (low-elevation subset only). Dep: sgp4.
- **Aircraft fuel burn context** — static endpoint `GET /api/static/fuel-burn` serves
  `data/_additional/aircraft_fuel_burn.json` (79 ICAO type codes → name/galph/category).
  OpenSky detail panel displays `FUEL  X gal/hr` when the watchlist `ac_type` field has a match.

### Code cleanup

- Removed `is_quarantined` property from `ProxyEntry` — logic was inverted
  (`time.monotonic() >= quarantined_until` returns True when the quarantine has expired,
  not when active). `ProxyPool.available_count()` uses the correct raw condition directly.
- Removed unused `compact_text()` from `scripts/generate_master_json.py`.
- `whitelist_vulture.py` updated: added `vessel_watchlist_alerts`, `aircraft_fuel_burn_rates`,
  `vessel_zone_alerts`, and `ProxyPool.available_count` to suppress false-positive vulture
  warnings on FastAPI route handlers and public pool interface methods.

---

## v1.21.0 — 2026-03-28

Progressive zoom disclosure, convergence contributor breakdown, and vessel-in-zone correlation.

### UX

- **Progressive zoom disclosure** — AIS, OpenSky, and VIIRS markers are suppressed when map
  zoom < 4 (world view). Event index and sessionStorage cache are still populated so
  convergence scoring and search remain accurate. A `zoomend` handler replays
  `sessionStorage.getItem("pt:ev:{source}")` on threshold crossing, so markers appear
  instantly without an extra network round-trip.
- **Convergence contributor breakdown** — "Contributing Evidence" section of the convergence
  cell popup now renders each signal family's event count (`×N`) and up to 3 contributing
  event IDs. Backend `contributors[].event_ids` was already populated; only the frontend
  rendering was updated.

### Backend

- **Vessel-in-zone correlation** — `api/routes/vessels.py` now runs Shapely
  `point.within(polygon)` at serve time. The `GET /api/vessels/sanctioned` response includes
  `zone_id` and `zone_name` for every FleetLeaks vessel inside a TankerTrackers risk polygon.
  New endpoint `GET /api/vessels/zone-alerts` returns LNG/tanker vessels inside the
  Hormuz, Bab-el-Mandeb, and Suez zones. Zone index is cached with a 5-minute TTL at
  module level; rebuilt transparently on cache expiry.

---

## v1.20.1 — 2026-03-28

Neon marker polish and watchlist labels bug fix.

### Bug fixes

- **Watchlist fallback to planes_master** — `get_aircraft_match()` now falls back to
  `planes_master.json` for ICAOs absent from `plane_alert_db`. Records are returned only when they
  carry at least a `category` or `tags` value; un-enriched Mictronics-only entries are excluded.
  Previously, aircraft enriched via the scripts but not present in the raw upstream list showed no
  category, no labels, and no neon marker in the live feed.

### UI

- **Neon sign marker style** — tracked/interesting aircraft markers now render with a five-layer
  drop-shadow glow (2 px tight core + 6/14/28/48 px spread) instead of three layers; outer spread
  at 48 px and higher per-layer alpha values produce the saturated tube-light look of real neon
  signage. `--tracked` outer ring gains a `box-shadow` halo to reinforce the neon tube outline.
- **Flicker animation** — `acNeonPulse` updated with irregular dim keyframes at 18 %, 20 %, 59 %
  that briefly drop opacity to 0.55 / 0.68 / 0.78 before snapping back; matches the momentary
  flicker characteristic of real neon gas discharge tubes.
- **Tracked icon size** — scale multiplier increased from 1.5x to 1.65x; rings expand to 1.85x
  (previously 1.65x) with a slightly faster cycle (2.2 s vs 2.4 s).

---

## v1.20.0 — 2026-03-28

Aircraft markers, UI polish, and full tag database update.

### UI fixes

- **Dark element cleanup** — four leftover dark-background components converted to light-theme surfaces:
  aircraft alert banner, VIIRS proximity banner, weather mesh legend, and MODU cluster tooltip.
  All now use `--panel-backdrop` / `--border` CSS variables with appropriate coloured borders.
- **Aircraft alert banner** — background changed from `rgba(20,0,0,0.92)` to `rgba(254,242,242,0.97)`;
  text updated to dark-on-light (`#991b1b`) for legibility on the light cartographic theme.
- **VIIRS proximity banner** — same light-surface treatment with orange tint and dark text.
- **MODU cluster tooltip** — removed dark charcoal fill; arrow pseudo-elements updated to match.

### Aircraft markers

- **Normal aircraft no longer pulsate** — `acNeonPulse` and `acNeonRing` animations removed from
  `.ac-neon-core` / `.ac-neon-ring` base classes; aircraft render as static category-colored icons.
- **Tracked (watchlist) aircraft pulsate with their category neon color** — new `.ac-neon-marker--tracked`
  CSS modifier re-enables both animations scoped to matched aircraft only.
  Previously, watchlist aircraft used a hardcoded red icon; they now inherit the full `_AC_CAT_STYLE`
  color palette (rotorcraft teal, heavy amber, UAV green, etc.) while still pulsating.
- `createWatchlistAircraftIcon` render path replaced by `aircraftIcon(..., isTracked=true)`.

### Aircraft database

- **15,636 records updated** across `planes_master.json` and `plane_alert_db.json` via TAGS_REVIEW.csv.
  1,298 replacement rules applied; tags consolidated into structured categories
  (Cargo & Transport, Emergency & Rescue, Military, Surveillance & ISR, etc.).
- `scripts/replace_flagged_tags.py` refactored — replacements now read directly from TAGS_REVIEW.csv
  rather than a hardcoded dict; any future CSV edits are applied by re-running the script.

---

## v1.19.0 — 2026-03-28

Professional UI overhaul: light map theme, source-differentiated aircraft icons,
detail panel source accents, inactive layer pruning, and interactive legend.

### Map and visual theme

- **Light map base layer** — switched from CartoDB Dark Matter to CartoDB Positron.
  The dark aesthetic was driving visual comparisons to consumer "vibe-coded" dashboards;
  Positron is the standard for professional GIS, journalism, and analytical tools.
- **Source colors recalibrated** — all `SOURCE_COLORS` values shifted 2-3 stops darker
  on the Tailwind scale so markers remain legible against white tile backgrounds.
  Previous neon values (#86efac, #c4b5fd, etc.) were optimised for dark maps only.
- **Popup and panel shadows** — reduced from `rgba(0,0,0,0.6)` (nightclub) to
  `rgba(0,0,0,0.14)` (document). All surface backgrounds converted to `--surface`
  (`#ffffff`) with `--border` dividers.
- **Full CSS custom property audit** — fixed search inputs, layer count badges, health
  badge text colors, attribution widget, mobile panel gradient, and legend badges
  that were all hardcoded for dark backgrounds and illegible on the new light theme.

### Aircraft icons

- **ADS-B category differentiation** — `_AC_CAT_STYLE` table maps all 12 ADS-B
  emitter categories (0-15) to distinct icon size, pulse ring diameter, and color.
  Heavy airframes (cat 4-5) render at 18-20 px with 30-34 px pulse rings; light GA
  aircraft (cat 2-3) render at 14 px with 20 px rings; military/special (cat 7, 15)
  use the largest icons with high-visibility orange/violet.
- **Neon pulsating rings** — each aircraft marker shows two concentric expanding rings
  (`acNeonRing` keyframe animation, 2.4s cycle with 0.8s phase offset) so individual
  aircraft are identifiable in dense clusters at low zoom.
- **Stale aircraft** — aircraft exceeding the stale threshold now render in `#b91c1c`
  at reduced icon size with no pulse, distinguishing them from live contacts at a glance.
- **Reduced-motion support** — `@media (prefers-reduced-motion: reduce)` suppresses
  all aircraft pulse animations without removing icon color differentiation.

### Detail panel

- **Source accent strip** — detail panel now injects a `--detail-color` CSS custom
  property on the content wrapper, set to the source's `SOURCE_COLORS` value.
  A left border, source ID badge, and the `.pt-header` color all derive from one
  variable — no per-source conditional code.
- **Confidence badge tint** — `.pt-conf` background uses `color-mix(in srgb,
  var(--detail-color) 12%, transparent)` so the tint tracks the source color
  automatically for every source type.
- **Source ID badge** — a `pt-source-id` element above the event title names the
  source in uppercase mono, making provenance visible without opening the health panel.

### Sidebar and layer controls

- **Inactive layer collapse** — layer toggles with zero-count and unchecked state
  are now hidden by default (`data-inactive="true"`). A footer link — "show N
  inactive" — reveals them without requiring any HTML template changes.
  Active, degraded, and non-zero layers are always visible.
- **Interactive legend** — hovering a source row in the legend dims all non-matching
  map markers to 0.06 opacity, isolating that source's spatial footprint without
  toggling layers. Mouseleave restores prior opacity state, respecting any active
  search query dimming.

### Infrastructure icons

- **Datacenter icon size** — increased from 8 px to 11 px square for legibility
  at zoom levels below 6.

---

## v1.18.0 — 2026-03-28

VIIRS proximity detection overhaul: fix the time window bug that prevented
alerts from ever firing, add server-side webhook dispatch with deduplication
and a persistent audit log, and correct offshore thermal scoring.

### VIIRS notification system

- **Fix: time window bug** — `max_age_minutes` default changed from 5 to 1440
  (24 h) in both the API endpoint and the frontend poll URL.  VIIRS NRT data
  arrives with 3-24 h satellite latency; the previous 5-minute window reliably
  returned zero detections.
- **New: env-configurable defaults** — `VIIRS_MAX_AGE_MINUTES` and
  `VIIRS_ALERT_RADIUS_KM` environment variables control the scan window and
  proximity radius without requiring code changes.  `le` upper bound on
  `max_age_minutes` raised from 60 to 43200 (30 days) to allow retroactive
  scans.
- **New: server-side alert dispatch** — new `core/alert_dispatch.py` module
  provides `ViirsAlertDispatcher`, a singleton that tracks dispatched event IDs
  with a 24-hour rolling TTL.  Each scheduler tick (every 5 minutes) evaluates
  the current proximity results and dispatches only unseen significant alerts.
- **New: webhook relay** — set `VIIRS_WEBHOOK_URL` to receive a JSON POST for
  each new significant alert.  Delivery failures are logged as warnings and
  never block the dispatch loop.
- **New: JSONL audit log** — every dispatched significant alert is appended to
  `data/viirs_alert_log.jsonl` so operators retain a durable record across
  server restarts.  Path is overridable via `VIIRS_ALERT_LOG_PATH`.
- **New: scheduled dispatch job** — `_run_viirs_alert_dispatch()` added to
  `api/scheduler.py` and registered at 5-minute intervals, aligned with the
  fast collector cycle.

### Offshore thermal scoring fix

- Offshore (`FP_type=3`) and gas-flare detections now only receive the -3
  noise penalty when they are more than 10 km from the nearest facility.
  Previously the penalty was always applied, causing a HIGH-confidence offshore
  thermal 2 km from a subsea cable to score 5 (below the 6 threshold) and be
  incorrectly suppressed.
- `_viirs_is_significant` updated to use the elevated threshold (score >= 9)
  only for distant offshore/gas-flare detections; close-range anomalies use the
  standard threshold (score >= 6).

### OpenSky resilience

- **New: persistent aircraft state cache** — new `collectors/opensky/opensky_cache.py`
  writes a JSON snapshot to `data/opensky_aircraft_cache.json` after every
  successful live fetch, keyed by collection timestamp.
- **Degraded-mode fallback** — when the OpenSky REST API is unavailable or
  returns an HTTP error, the collector serves from the last good cache and
  sets `CollectorRunStatus("degraded", "cache", ...)` so the health panel
  reflects the real state instead of showing the source as "down".
- **Time-filtered playback** — cached state vectors older than
  `OPENSKY_CACHE_PLAYBACK_MINUTES` (default 15) are excluded from cache
  responses so stale positions never appear on the map.
- **Cache staleness guard** — if the cache file is older than
  `OPENSKY_CACHE_MAX_AGE_SECONDS` (default 3600), the collector marks itself
  "down" rather than serving hour-old aircraft positions as live data.
- **Rate-limit back-off** — HTTP 429 responses now trigger a
  `_rate_limited_until` timer (parsed from `X-Rate-Limit-Retry-After-Seconds`
  header; default 60 s).  Subsequent calls within the back-off window are
  served directly from cache with no outbound request.
- **Anonymous-first request strategy** — unauthenticated access is attempted
  first on every poll cycle, saving the token round-trip when the anonymous
  credit quota is sufficient.  OAuth2 escalation occurs only on 401/403.
- **New env variables** — `OPENSKY_CACHE_PLAYBACK_MINUTES`,
  `OPENSKY_CACHE_MAX_AGE_SECONDS` control cache behaviour without code changes.

### Collector polling intervals

Moved four sources from the 5-minute fast loop to individual slow-schedule
jobs appropriate for their actual data update frequency.

| Collector | Old interval | New interval | Rationale |
|---|---|---|---|
| VIIRS | 5 min | 30 min | NASA NRT delivery latency is 3-24 h |
| NDBC buoys | 5 min | 30 min | NDBC standard files update hourly |
| NGA DailyMem | 5 min | 60 min | Daily NGA broadcast batch |
| NGA MIS | 5 min | 15 min | Maritime safety notices update infrequently |

The fast 5-minute loop now contains only genuinely real-time sources: AIS
vessel tracking, OpenSky aircraft, FAA NOTAMs, and SWPC space weather.

### Code structure

- Core proximity logic extracted into `compute_viirs_proximity_alerts()` in
  `api/routes/intel.py` so the endpoint and the dispatch job share identical
  detection logic without duplication.
- `_run_slow_streaming()` helper added to `api/scheduler.py` for streaming
  sources (non-REF) on slow schedules; uses `store.add_events` instead of
  `store.replace_ref_events`.
- `_run_nga_mis_slow()` replicates the mixed-source dispatch logic from
  `_run_all_collectors` so SMAPS and NGA MIS events are routed to the correct
  store tier independently.

---

## v1.17.3 — 2026-03-27

Stable patch release for proximity-query triage and health-state verification.

### Proximity query triage

- Right-click proximity results now render as structured tables with explicit
  distance, source, signal, and observed-time columns instead of an unlabelled
  list.
- Proximity scans now surface nearby datacenter reference hits even when the
  datacenter layer is not enabled, capped with explicit "showing X of Y"
  disclosure in dense metros.

### Health-state verification

- Added API regression coverage proving NOTAM cache-backed runs surface as
  degraded in `/api/health/sources`.
- Added API regression coverage proving mixed MIS runs and SMAPS cache
  fallback surface through `/api/intel/mis-status`.

### Release sync

- Synced internal/public README, CHANGELOG, roadmap, frontend version badge,
  FastAPI app version, and package version to `v1.17.3`.
- Release checkpoint tag: `checkpoint-2026-03-27-v1.17.3-release`.

## v1.17.2 — 2026-03-27

Stable patch release for operator workflow honesty and banner usability.

### Alert banner workflow

- Moved the aircraft and VIIRS alert banners out of the map overlay and into
  page flow below the top bar, so compact screens no longer cover zoom and
  layer controls.
- Fixed banner dismissal behavior: closing the current aircraft or VIIRS alert
  now persists across refresh cycles until a new alert supersedes it.
- Tightened banner click handling so the close button cannot fall through into
  the banner's map-jump action.

### Operator state disclosure

- `/api/events/geojson` now returns `total_count`, `returned_count`, `limit`,
  and `truncated` metadata so capped map feeds can disclose partial state.
- Layer toggles now mirror source health directly with cache, stale, and down
  badges instead of hiding that information in the health panel alone.
- Layer-count badges and the sidebar layer note now disclose "showing X of Y"
  when a source layer is capped by API limits.

### Release sync

- Synced internal/public README, CHANGELOG, roadmap, frontend version badge,
  FastAPI app version, and package version to `v1.17.2`.
- Release checkpoint tag: `checkpoint-2026-03-27-v1.17.2-release`.

## v1.17.1 — 2026-03-27

Reference data enrichment and overlay schema normalisation.

### Aircraft watchlist additions

- Added 4 new entries to `plane_alert_db.json` (total: 16,010):
  - Roman Abramovich: `4D0225` LX-GVI (Gulfstream G650) and `4D0228` LX-LUX
    (Bombardier Global 6000) — present in Phaeton source but previously missing.
  - Bahrain Royal Flight: `894082` A9C-HAK (Boeing 747-400) — sourced from
    geneva-dictators dataset.
  - Russia Special Detachment: `155BD0` RA-89040 (Sukhoi Superjet 100-95) —
    sourced from geneva-dictators dataset.

### New reference data file

- Added `data/_additional/aircraft_fuel_burn.json` — 79 ICAO type codes with
  fuel consumption (gallons/hour) and size category. Sourced from
  `Jxck-S/plane-notify`. Enables carbon/cost context in aircraft detail panels.

### Overlay schema normalisation

- Fully rewrote `data/_additional/strategic_overlay_geocoded.json`: all records
  now have consistent `name` (human label) and `type` (snake_case code) fields.
  Previous schema mixed type-as-name strings (e.g. `"type": "OTH Radar China"`)
  with code values. Section keys renamed to professional equivalents:
  `rf_emitters` → `rf_infrastructure`, `sanctions_entities` →
  `maritime_compliance_nodes`, `weather_constraints` → `weather_zones`,
  `behavioral_patterns` → `ais_anomaly_zones`, `cyber_physical_targets` →
  `cyber_physical_infrastructure`.

### Additional data category cleanup

- `yacht_alert_db.json`: collapsed `"Celebrity / Mogul"` and `"Tech Billionaire"`
  into `"Notable Private Owner"` for consistent professional language.
- `tracked_names.json`: renamed `"YouTubers"` → `"Aviation Content Creator"` and
  `"People"` → `"Notable Individual"` across both `names` list and `details`
  dict (214 entries updated).

### Housekeeping

- Removed stale backup files: `plane_alert_db.json.bak`, `planes_master.json.bak`,
  and two timestamped backups in `data/_additional/backups/`.

### Validation

- `python3 -m json.tool` clean on all modified JSON files.
- Release checkpoint tag: `checkpoint-2026-03-27-v1.17.1-release`.

---

## v1.17.0 — 2026-03-27

Aircraft catalog enrichment, binary search on click, and data sanitization.

### Aircraft catalog enrichment

- Added `GET /api/static/aircraft/{icao}` — direct O(1) lookup against the
  aggregated `planes_master.json` catalog (cached in memory). Returns 404 when
  the ICAO is not in the catalog.
- Added `GET /api/static/aircraft-index` — returns the full sorted list of
  catalog ICAOs for frontend binary-search membership checks.
- Clicking any OpenSky aircraft now enriches the detail panel on demand: the
  frontend performs a binary search against the pre-loaded ICAO index and
  fetches the full catalog record only when a match is found, adding no latency
  for unlisted aircraft.

### Detail panel and search result improvements

- Aircraft category now renders as a styled badge rather than plain text.
- Tags now render as individual label chips in both the detail panel and the
  catalog search result list.
- Catalog search results show the category badge, aircraft type, and up to four
  tag chips per result.
- Fixed the aircraft profile section inside the Leaflet popup balloon: key/value
  rows were rendering without layout (labels and values running together) because
  the flex rules were only scoped to `.pt-popup` and `.detail-content`, not to
  `.ac-popup`. Added the full row/key/val rule set under `.ac-popup`.

### Aircraft database sanitization

- Replaced 26 informal category names sourced from the original plane-alert-db
  project with professional equivalents across both `plane_alert_db.json` and
  `planes_master.json`. Examples: "Toy Soldiers" → "Army Aviation", "Ptolemy
  would be proud" → "Aerial Survey", "Flying Doctors" → "Medical Air Services",
  "Oxcart" → "Reconnaissance & ISR", "Gas Bags" → "Lighter-Than-Air".
- Corrected a mis-mapping: "Climate Crisis" was wrongly mapped to "Environmental
  Monitoring" (weather aircraft). These are corporate and private jets; remapped
  to "Corporate & Private Aviation".
- Renamed "GAF" to "German Air Force" for clarity.
- Removed politically motivated and joke tags: "Man Made Climate Change",
  "Climate Crisis" (tag), "How The Other Half Live", "Not A Car", and others.
- Replaced slang tags with professional equivalents: "Police Squad" →
  "Law Enforcement Aviation", "Copper Chopper" → "Police Helicopter", "Mae West"
  → "Maritime Safety Equipment", "In The Navy" → "Naval Aviation", "War Bird" →
  "Historic Military Aircraft".

### Validation

- Ruff check on modified backend files → clean.
- Release checkpoint tag: `checkpoint-2026-03-27-v1.17.0-release`.

---

## v1.16.4 — 2026-03-27

Slow-layer recovery, runtime-data persistence hardening, and container
priority tuning.

### Slow collector and map-layer fixes

- Fixed `tankertrackers_seized` showing `0` after fresh container starts by
  accepting the upstream JSON envelope shape and scheduling an immediate
  startup run for the seized-vessel collector.
- Fixed `neracoos` map-layer failures where GeoJSON serialization received raw
  Python `datetime` objects, returning HTTP `500` and leaving moorings empty in
  the UI.
- Kept `neracoos` visible as a stale-but-valid reference layer by preserving
  `max_age_days=0` handling in the frontend map fetch path and surfacing its
  degraded state honestly in source health.

### Container data policy and performance

- Added `core.runtime_data` startup seeding so bundled read-only assets are
  copied into the persistent `/app/data` volume only when missing, rather than
  overwriting existing runtime data on rebuild.
- Added a Docker entrypoint sync step and enabled `SYS_NICE` capability so the
  configured `renice` hook now applies to the running app process.
- Documented the runtime-data persistence contract and screenshot-refresh
  discipline in the roadmap.

### Validation and release hygiene

- Added targeted regression coverage for runtime-data seeding and NERACOOS
  timestamp normalization.
- Validation: targeted `pytest` selection -> `18 passed`; touched-file `ruff
  check` -> clean; live container verification -> `tankertrackers_seized=10`,
  `neracoos=6`.
- Release checkpoint tag: `checkpoint-2026-03-27-v1.16.4-release`.

---

## v1.16.3 — 2026-03-27

Docker-safe static data packaging, bundled fallback resolution, and release checkpoint.

### Container packaging and static-layer fixes

- Fixed containerized deployments where the writable `/app/data` volume masked
  bundled reference datasets, leaving `strategic-overlay`, `datacenters`,
  `nuclear-plants`, and dependent infrastructure context APIs empty even
  though local dev rendered correctly.
- Added `core.data_paths.resolve_data_path()` and
  `resolve_additional_data_path()` so read-only release assets can fall back to
  `/app/bundled_data` when runtime volumes overlay `/app/data`.
- Routed static-layer APIs, VIIRS proximity facility loading, watchlist
  database loading, and NOTAM airport lookup through the new resolver.
- Updated Docker packaging to include `data/_additional` and `airports.json`
  in the image build, then copy them into `/app/bundled_data` for runtime use.

### Validation and release hygiene

- Added regression coverage for primary vs fallback bundled-data resolution.
- Validation: targeted `pytest` selection -> `9 passed`; targeted `ruff check`
  on changed Python modules -> clean.
- Release checkpoint tag: `checkpoint-2026-03-27-v1.16.3-release`.

---

## v1.16.2 — 2026-03-27

Strategic overlay normalization, infrastructure-aware VIIRS proximity, and
static-layer rendering diagnostics.

### Infrastructure layer fixes

- Added `GET /api/static/strategic-overlay`, merging three internal reference
  datasets: `strategic_overlay_geocoded.json`,
  `invisible_infrastructure_overlay.json`, and
  `clair_critical_infrastructure_2026.geojson`.
- Mixed `_additional` schemas are now normalized to one GeoJSON-style feature
  contract. Cables and pipelines emit both corridor `LineString` geometry and
  landing-point or node markers, so the overlay can show paths and points at
  the same time.
- `GET /api/static/nuclear-plants` and `GET /api/static/datacenters` now emit
  explicit point geometry. The frontend no longer depends on raw `lat` / `lng`
  fields for those static layers.
- Added a Strategic Overlay toggle to the frontend and switched static-layer
  rendering to geometry-first coordinate extraction. This fixes the frontend /
  backend schema mismatch that was leaving land-based features and datacenters
  invisible.
- Datacenter rendering was widened slightly for operator use: lower zoom gate
  (`4.5`), larger icons, and restored persisted toggle state on boot.

### VIIRS proximity and analyst workflow

- `GET /api/intel/viirs-proximity-alerts` now scans military bases and eligible
  strategic overlay nodes in addition to nuclear facilities and datacenters.
- Proximity responses now include `layer`, `feature_id`, `role`,
  `source_name`, and `groups_enabled`, making alert attribution explicit.
- The VIIRS proximity banner now identifies the nearest infrastructure class
  and reveals the relevant context layer on click instead of only panning to
  the thermal event.
- Default proximity radius increased from `25 km` to `40 km`.
- Fixed a route bug where VIIRS events from the store were being treated like
  attribute objects instead of mappings.

### Diagnostics and validation

- Added optional frontend debug mode: `?debug_static_layers=1` or localStorage
  key `pt:debug:static-layers=1`. It logs static-layer load / render counts and
  surfaces inline notes for strategic overlay and datacenter rendering.
- Added API test coverage for strategic overlay normalization, static geometry
  output, and VIIRS proximity matching against strategic infrastructure.
- Validation: `python3 -m pytest -q` -> `153 passed`.

---

## v1.15.0 — 2026-03-27

New intelligence layers (USGS, ECCC, EMODnet, nuclear), VIIRS proximity alert,
and three data-pipeline bug fixes.

### Bug fixes

- **NERACOOS collector crash** (`CollectorRunStatus` bad kwargs): `NeraCOOSCollector`
  was calling `CollectorRunStatus(source=SRC_NERACOOS, event_count=len(events), …)`
  which raised `TypeError` on every run because the dataclass only accepts
  `status`, `run_mode`, `detail`. Both call sites (live + cache-fallback paths)
  corrected. NERACOOS status is now `ok` / `degraded` / `cache` as intended.

- **USGS and ECCC event counts always 0 in health**: `count_events_by_source()`
  in `core/store.py` checks `REF_SOURCES` to decide which internal store to query.
  `"usgs"`, `"eccc"`, and `"neracoos"` were missing from the frozenset so every
  count query searched the streaming deque (finding nothing). All three sources
  added to `REF_SOURCES`. Health panel now reports accurate event counts.

### New collectors

- **USGS earthquake feed** (`collectors/usgs/usgs_quake_collector.py`): M2.5+
  earthquakes worldwide from the USGS GeoJSON summary feed. Schedule: 15 min.
  Attributes: magnitude, depth_km, place, tsunami flag, PAGER alert level, USGS
  event URL. Convergence weight: M5.5+ within 36h adds weight 1.5 to cells sharing
  the same cell. Colour: #a78bfa (violet).

- **ECCC marine weather** (`collectors/eccc/eccc_marine_collector.py`): Environment
  and Climate Change Canada real-time marine weather warnings covering the Gulf of
  St Lawrence, Hudson Bay, and Canadian Arctic — waters not covered by NDBC.
  Schedule: 30 min. Attributes: warning_name, severity, region, area, effective_time.
  Convergence weights: storm/hurricane warning → 2.0, gale/freezing spray → 1.5
  within 48h. Colour: #67e8f9 (sky blue).

### New frontend layers

- **USGS map layer**: magnitude-scaled star icons (10 px < M5, 16 px M5+, 22 px M6.5+).
  Popup: magnitude badge, depth, place, tsunami flag, PAGER alert chip, USGS link.
  Layer exempt from time-window filter (snapshot data).

- **ECCC map layer**: standard 18 px pin. Popup: warning name header, severity chip
  colour-coded by severity (red = storm/hurricane, orange = gale, blue = freezing
  spray), area, region, effective time. Layer exempt from time-window filter.

- **EMODnet Human Activities overlay**: toggleable WMS layer group over European
  waters showing submarine cables, oil/gas pipelines, and offshore wind farm
  polygons. Pure frontend — no collector, no backend change. Toggle added to map
  controls panel; preference persisted to localStorage.

- **Nuclear facilities reference layer** (toggle: "Nuclear plants"): power_plants.json
  filtered to `fuel_type == "Nuclear"` (~250 records). Rendered as radioactive-glyph
  markers. Static reference data; labelled clearly in popup.

### New endpoint

- `GET /api/intel/viirs-proximity-alerts?max_age_minutes=5&radius_km=25`
  Scans VIIRS thermal detections (VIIRS_FIRE + VIIRS_DNB) from the last N minutes
  and returns any that fall within radius_km of a nuclear plant, coastal datacenter,
  or military base. Haversine distance computation; module-level facility cache to
  avoid reloading 5000+ datacenter records per request. Response includes per-alert
  nearest facility name, type, country, distance_km, and all_nearby list.

### New frontend alert banner

- `#viirs-proximity-banner`: orange-themed alert banner (positioned below aircraft
  alert banner) shown whenever the `/api/intel/viirs-proximity-alerts` endpoint
  returns at least one alert in the last 5 minutes. Displays event count and nearest
  facility name with distance. Click handler enables the VIIRS layer and pans to
  the nearest detection. Wired into `refreshAll()` on every 30-second cycle.

### Convergence scoring additions

- `usgs_seismic_significant` contributor: M5.5+ USGS quake within 36h → weight 1.5.
- `eccc_storm_warning` contributor: ECCC storm/hurricane warning within 48h → weight 2.0.
- `eccc_gale_warning` contributor: ECCC gale/freezing spray within 48h → weight 1.5.

### Screenshots

- `docs/screenshots/take_screenshots.py` updated: `ctx.add_init_script()` now
  injects `localStorage.setItem('pt:onboarding:v1','1')` before first navigation
  so the onboarding modal never appears. Fixed `void map.setView(…)` to prevent
  Playwright serialization error on Map object return. Target changed to
  `http://localhost:8000`. Twelve screenshots retaken.

---

## v1.14.0-dev — 2026-03-26

Aircraft watchlist intelligence layer (Phase 5.5 core)

### New: `core/watchlist.py` — static watchlist registry

- Loads four databases from `data/_additional/` at import time (singleton, no per-request
  overhead): `plane_alert_db.json` (16,006 ICAO hex records), `tracked_names.json` (726
  operator entries), `plan_ccg_vessels.json` (92 PLAN/CCG MMSIs), `yacht_alert_db.json`
  (12 notable yacht MMSIs), `military_bases.json` (647 geocoded installations).
- Public API: `get_aircraft_match(icao24)`, `get_vessel_match(mmsi)`,
  `match_tracked_operator(operator)`, `stats()`, `MILITARY_BASES`.

### OpenSky collector enrichment

- `_state_to_event()` now calls `get_aircraft_match(icao24)` for every state vector.
- Matched aircraft receive `attributes.watchlist_match` dict containing: registration,
  operator, ac_type, category, tags, link, watchlist_db, icao24.
- No overhead for unmatched aircraft (dict lookup, O(1)).

### AIS collector enrichment

- `_raw_to_event()` now calls `get_vessel_match(mmsi)` for every position report.
- PLAN/CCG vessels and notable yachts receive `attributes.watchlist_match` at ingest.

### New API routes

- `GET /api/intel/aircraft-alerts?limit=N` — returns current OpenSky events where
  `attributes.watchlist_match` is set. Response includes count, spotted_count (unique
  ICAO addresses), category breakdown, and full alert rows.
- `GET /api/military-bases` — static military installation feature list (647 records,
  each: name, country, operator, branch, lat, lng).
- `GET /api/watchlist/stats` — database sizes for health dashboard use.

### Frontend

- `createWatchlistAircraftIcon(rawValue)` — pulsating red SVG aircraft marker using CSS
  `@keyframes wlAircraftPulse` (drop-shadow glow, 1.4s cycle, respects prefers-reduced-motion).
- Watchlist aircraft in `_applyEventFeatures`: `_isWatchlistAircraft` flag derived from
  `attributes.watchlist_match`; fill forced to `#ef4444`; `createWatchlistAircraftIcon`
  used instead of `aircraftIcon`; fast-path icon update path updated to match.
- `#aircraft-alert-banner` — absolutely positioned overlay at top-centre of map, shown
  when any tracked aircraft are currently spotted. Displays count and up to 4 aircraft
  labels (registration + category).
- `loadAircraftAlerts()` + `updateAircraftAlertBanner()` — fetch `/api/intel/aircraft-alerts`
  on every `refreshAll` cycle, update banner state.
- `state.militaryBasesLayer` + `state.militaryBasesSnapshot` — dedicated layer group for
  military base markers. Loaded lazily on first toggle-on.
- `loadMilitaryBases()` + `renderMilitaryBasesLayer()` — fetch `/api/military-bases`, render
  12px red star markers with tooltip. Default off; toggle under map layers.
- `fShowMilitaryBases` checkbox + toggle handler wired. UI pref restore added.
- `API.aircraftAlerts`, `API.militaryBases` constants added.
- CSS: `@keyframes wlAircraftPulse`, `.wl-aircraft-pulse`, `#aircraft-alert-banner`,
  `#aircraft-alert-banner.is-visible`, `.ab-count` all added to `style.css`.

---

## v1.13.0 — 2026-03-26

Sprint B frontend, NERACOOS mooring collector, maintenance tax TAX 1/2/3

### Maintenance (TAX 1/2/3) — no behaviour changes

- **TAX 1 — app.py preload factory**: replaced 8 near-identical `_preload_*_cache()`
  functions with a `_REF_PRELOADS` registry (list of 7 tuples) + one generic
  `_preload_ref_cache()` driver. SMAPS kept its own function (two-stage transform).
  Adding a new REF_SOURCE collector is now 1 tuple, not 1 new function.

- **TAX 2 — scheduler slow-collector wrappers**: replaced 9 manual `pop`/`add_job`
  blocks in `start_scheduler()` with `_build_slow_collector_jobs()` table.
  Collapsed 4 identical standard wrappers (guide, marad, zones, seized) into
  `_run_standard_ref_slow()`. Adding a new slow collector = 1 table entry.

- **TAX 3 — app.js section boundary map**: 35-entry module boundary comment block
  added at top of `frontend/js/app.js` listing start line of every logical section.
  File grew from 5619 → 5876 lines with Sprint B additions; map keeps it navigable.

### New collector — NERACOOS/ERDDAP moorings

- `collectors/neracoos/neracoos_collector.py`: fetches latest observations from
  6 NERACOOS fixed moorings in the Gulf of Maine / Northwest Atlantic via the
  ERDDAP tabledap REST API (no auth, JSON format).
  - Stations: A01 (met), A01_waves (wave strain gauge), B01 (met), E01 (met),
    M01 (CTD 200 m depth), N01 (met)
  - Attributes per station: air temperature, wind speed/direction, pressure,
    significant wave height, wave period, sea water temperature, salinity (PSU)
  - Source: `neracoos` | event type: `neracoos_mooring` | schedule: 60 min
  - File cache fallback: `data/neracoos_cache.json`
  - Frontend: emerald square markers, dedicated popup with all available fields

### Sprint B frontend — sanctioned fleet, zones, seized vessels

- **Sanctioned vessel layer** (`fleetleaks`): amber triangle markers. High-spoof
  vessels (spoofing_score >= 2) get a dashed red outer ring via
  `createSpoofingBorderIcon()`. Fill turns red for score >= 2.
  Popup: vessel name, IMO, type, flag, AIS status, sanctioners, spoofing score,
  per-agency sanction dates.

- **TankerTrackers maritime risk zones**: orange polygon overlay loaded from
  `/api/zones`. Toggle: "Maritime risk zones" (default on). Zone name shown
  on hover tooltip. Layer sits above convergence risk zones, below markers.

- **Seized / Iran Navy vessel layer** (`tankertrackers_seized`): orange star
  for seized tankers, red star with white stroke for Iran Navy / IRGC assets.
  Popup: name, IMO, alert type, last-seen date, confidence note.

- All three new layers: added to `LAYER_NAMES`, `SOURCE_COLORS`, `SOURCE_SHAPES`,
  `STALE_THRESHOLDS`, time-window filter exemption (snapshot-style data).

### Data sources notes (notes.txt review)

- **NERACOOS/ERDDAP**: implemented (see above).
- **USDA NASS QuickStats**: agriculture data — no maritime relevance, deferred.
- **BigBodyCobain/Shadowbroker GitHub**: flagged for manual inspection before
  integration. The repository name is associated with a threat-actor group;
  contents must be reviewed by a human before any data is ingested.

---

## v1.12.0 — 2026-03-26

Sanctioned fleet cluster, core hardening, DEVELOPER_PLAN, test expansion

### New collectors — sanctioned fleet cluster (Sprint B + C)

- `collectors/fleetleaks/fleetleaks_vessels.py`: FleetLeaks live AIS snapshot
  for sanctioned fleet. Computes derived anomaly fields at collection time:
  `ais_position_precision` (whole-degree sentinel), `speed_anomaly` (vessel-type
  max speed exceeded), `heading_available` (heading sentinel 511), and
  `spoofing_score` 0–3 (sum of three flags). IMO-keyed sanctions data merged
  from TankerTrackers cache at collection time.
- `collectors/tankertrackers/tankertrackers_sanctions.py`: 1,370+ IMO-keyed
  sanctions registry (OFAC, EU, FCDO, GAC, SECO, UANI, ASO, UN) with per-agency
  sanction dates. Emits no EventRecords — lookup table loaded by FleetLeaks
  and the API sanctions endpoints.
- `collectors/tankertrackers/tankertrackers_zones.py`: 183 named maritime risk
  zone polygons (WKT). Strips `SRID=4326;` prefix; computes centroid lat/lon;
  emits one EventRecord per zone. Stored in ref_store for vessel-in-zone
  correlation.
- `collectors/tankertrackers/tankertrackers_lostandfound.py`: seized and
  Iran Navy vessel registry. Emits EventRecords with `status` field
  (`taken` / `iran_navy`); movement detection via position delta between polls.

### New API routes — vessels module

- `GET /api/vessels/sanctioned` — FleetLeaks snapshot with filters:
  `type`, `anomaly` (spoofing_score ≥ 2), `ais_status`, `sanctioner`
- `GET /api/vessels/sanctioned/{imo}` — single vessel by IMO
- `GET /api/zones` — TankerTrackers maritime risk zone list
- `GET /api/zones/{zone_id}` — single zone with WKT
- `GET /api/sanctions` — sanctions registry (paginated)
- `GET /api/sanctions/{imo}` — single vessel sanctions by IMO
- `api/routes/vessels.py` router mounted at `/api`, tagged `vessels`

### Scheduler integration

- All four new collectors registered in `api/scheduler.py`:
  FleetLeaks (5-min), TankerTrackers sanctions (60-min),
  TankerTrackers zones (24-hour), TankerTrackers seized (30-min).
- Cache preload on startup for FleetLeaks vessels and TankerTrackers zones.

### Core modules

- `core/dates.py`: centralised datetime parsing (7-tier pipeline: ISO → full DTG
  → short DTG → bare date → US slash date → US slash datetime → dateutil).
- `core/provenance.py`: `build_provenance()` helper for consistent provenance
  dicts across all collectors.

### Engineering

- `DEVELOPER_PLAN.md`: full implementation spec for all v2.0 new data sources
  (field schemas, TTLs, anomaly detection logic, unit test requirements).
- `Things I have found.txt`: live endpoint research notes.
- `tools/fill_notam_cache.py`: NOTAM cache warm-up utility.
- `whitelist_vulture.py`: vulture whitelist for FastAPI route false positives.
- Removed stale docs: `LAUNCH_BRIEF.txt`, `NEW_SOURCES_REVIEW.txt`,
  `PLATFORM_REVIEW_2026-03-21.txt`.
- `.gitignore` extended: exclude data cache/snapshot/mtimes/jsonl files and
  VIIRS binary outputs.

### Tests

- 149 tests passing (up from 94). New test suites:
  `tests/fleetleaks/test_fleetleaks_vessels.py`,
  `tests/tankertrackers/test_tankertrackers_sanctions.py`,
  `tests/tankertrackers/test_tankertrackers_zones.py`,
  `tests/tankertrackers/test_tankertrackers_lostandfound.py`,
  `tests/core/test_dates.py`, `tests/core/test_geo_extract.py`,
  `tests/test_guide_provenance.py`.

---

## v1.11.0 — 2026-03-26

Data freshness, parsing reliability, and source resilience

### Data quality

- GUIDE GPS disruption collector: corrected column mapping that caused all 448
  historical events to carry the collection timestamp instead of the actual
  report-opened date. All GUIDE events now reflect the real GPS disruption date.
- GUIDE heatmap extraction: robust against page variants that emit a flat numeric
  array instead of nested arrays. Both forms parsed into expected `[lat, lon, ts, id]`.
- `core/dates.py`: added step-6 parser for USCG NAVCEN GUIDE `MM/DD/YYYYhh:mm:ss [TZ]`
  format (date+time concatenated, optional multi-word TZ name). Pipeline order is now:
  ISO → full DTG → short DTG → bare date → US slash date → US slash datetime
  → dateutil → dateparser.
- `core/convergence.py` and `core/rules.py`: replaced inline `fromisoformat` with
  `parse_datetime` so timestamp comparison is consistent across the platform.

### Coordinate extraction

- `core/geo_extract.py`: added three new extraction patterns with overlap guards:
  LAT/LON labeled with hemisphere, LAT/LON labeled with sign, bare signed decimal pair.
  Decimal-point guard on the bare pair pattern reduces false positives against numeric text.
  All six formats documented in module docstring in priority order.

### Collector provenance and confidence

- MARAD collector: emits `field_confidence` (coords 0.6 if approx/0.2 if inferred,
  timestamp 0.85) and `provenance` on every event.
- NGA MIS (MODU) collector: emits `field_confidence` (lat/lon 0.95, timestamp 0.8)
  and `provenance` including raw MODU identifier.
- SMAPS collector: Playwright WAF fallback with structured retry logging.
  Cache-age validation uses `parse_datetime`.
- DailyMem and NDBC SAR2 collectors: cache-age validation uses `parse_datetime`.

### Bug fixes

- `core/convergence.py`: `EventRecord` import was removed during refactor; restored.
  Without it, any convergence scoring call raised `NameError` at runtime.
- `collectors/notam/notam_collector.py`: duplicate FIR→airport entries for ZNY/KZNY removed.
- `collectors/ndbc/ndbc_collector.py`: unused `prov_base` variable removed.
- `core/ch_store.py`: `zip()` made explicit with `strict=False`.

### Tests

- 94 tests passing. No regressions.

---


Datetime parsing hardening, coordinate extraction expansion, version alignment

### Features

- `core/dates.py` extended with military DTG support (`DDHHmmZ MON YY[YY]`), short DTG
  (`DDHHmmZ` anchored to current UTC month), bare date (`DD MON YY[YY]`), and US slash
  date (`MM/DD/YYYY`). `parse_datetime()` now resolves all seven tiers before returning None.
- `core/geo_extract.py` now extracts LAT/LON-labeled coordinates in both hemisphere
  (`LAT 33.7N LON 118.2W`) and signed (`LAT: -33.7 LON: -118.2`) forms, and bare signed
  decimal pairs (`33.7167, -118.25` or `33.7167 -118.25`).

### Bug fixes

- Version drift resolved: `pyproject.toml` and `api/app.py` both updated from `0.1.0`
  to `1.10.1` (now `1.10.2`).
- All raw `datetime.fromisoformat()` call sites in collectors and core modules replaced
  with `parse_datetime()` from `core.dates`, eliminating silent parse failures on
  non-ISO inputs and improving error handling consistency.
  Affected files: `dailymem_collector.py`, `mis_collector.py`, `marad_collector.py`,
  `ndbc_sar2_collector.py`, `core/rules.py`, `core/store.py`, `core/convergence.py`,
  `api/routes/health.py`.
- `collectors/guide/guide_collector.py` `_parse_date()` now uses `parse_datetime()`
  instead of a local `strptime` for `MM/DD/YYYY`, centralizing all date parsing.

### Engineering hygiene

- 27 new tests added: `tests/core/test_dates.py` and `tests/core/test_geo_extract.py`
  covering all new parsing formats and edge cases. Total test count: 94.
- `core/redis_store.py` `_to_score()` replaced raw `fromisoformat` with `parse_datetime()`.
- `api/routes/health.py` `GET /health` now returns `version` field from `app.version`,
  eliminating the hardcoded version string in the frontend HTML. The UI badge updates
  automatically on each page load.

---

## v1.10.1 - 2026-03-24

Intel table freshness and comprehensive sorting fixes

### Bug fixes

- Fixed intel tables refresh logic: tables now update on every 30-second refresh cycle regardless of panel visibility, eliminating stale data when reopening the intel panel.
- Fixed event sorting in store: `get_events()` now returns events sorted by timestamp (newest first), ensuring intel tables consistently show the most recent items at the top.
- Fixed hypothesis sorting: `get_hypotheses()` now returns hypotheses sorted by timestamp (newest first), ensuring the rule engine output shows latest evaluations first.
- Fixed GeoJSON sorting: `events_as_geojson()` now returns events sorted by timestamp (newest first), improving map display consistency.
- All store tests pass with the new sorting behavior, maintaining backward compatibility for existing API consumers.

### Engineering hygiene

- Simplified frontend refresh logic by removing conditional table loading, improving data consistency across the dashboard.
- Enhanced store reliability with deterministic event ordering across all retrieval methods, eliminating dependency on implicit insertion order assumptions.
- Ensured all intel table API endpoints (`/nav-warnings`, `/broadcast-warnings`, `/notams/critical`, `/gps-disruptions`, `/marad-advisories`, `/icc-piracy`) consistently sort results newest-first.

---

## v1.10.0 - 2026-03-23

ICC-CCS live piracy, first convergence release, and map-clarity improvements

### Sources and intelligence

- Added an ICC-CCS IMB piracy collector, API route, analyst table, and map layer so Phantom Tide now carries a live current-year piracy incident surface instead of relying on historical context alone.
- Added the first shipped convergence system: weighted multi-source cell scoring in `core/convergence.py`, a new `/api/convergence` endpoint, and dashboard rendering of scored convergence zones with contributor drill-down.

### Frontend and operator workflow

- Replaced the old heuristic client-side risk overlay with backend-scored convergence cells rendered directly on the map.
- Added sidebar status copy explaining how many convergence cells are visible at the current zoom and when lower-priority cells are intentionally hidden.
- Added an explicit warning when all source layers are enabled so operators know they are in the noisiest possible view state.
- Expanded dense-layer viewport culling beyond AIS/OpenSky/VIIRS to reduce unnecessary marker work when global layers are enabled together.

### Engineering hygiene

- Cleaned dead-code tooling output by whitelisting FastAPI decorator entry points and serializer-only model fields while removing genuinely unused constants and a stale convergence constant.
- Normalized backend import ordering, slice formatting, and test fixtures so the new source and convergence code paths stay consistent with the repo style baseline.

## v1.9.5 - 2026-03-23

MARAD, collector trust visibility, and fetch hardening

### Sources and intelligence

- Added a MARAD MSCI advisory collector, API route, and frontend table/layer so regional U.S. maritime threat advisories are now part of the live analyst surface.
- Added scheduler alerting when a collector misses repeated cycles, making quiet ingest failures visible before they age into stale data.

### Collection reliability

- WAF-facing HTML and RSS collectors now use shared browser-like rotating headers backed by `fake-useragent` instead of static application user agents.
- Slow reference collectors now expose honest run states through source health: live, cache-backed degraded, or empty / failed.
- GUIDE, MARAD, GPS advisory, and NDBC sar2 no longer appear silently healthy when they are serving cached data or have no usable fallback.

### Documentation

- Internal README now reflects MARAD as an active source, documents the MARAD intel endpoint, and records the new source-health behavior and remaining parity gaps.
- Internal release marker advanced to `v1.9.5`.

## v1.9.4 - 2026-03-22

Intel panel space use and footer legibility

### Dashboard UI

- Intel tables now keep a true two-panel layout on wide screens instead of collapsing into a left-weighted strip with unused columns.
- The queued-briefings toolbar now sits above a dedicated briefing grid, so the active briefing cards take the available height instead of sharing grid space with the toolbar.
- Active briefing cards now have a larger minimum height, making low-row-count panels feel intentional rather than stranded in empty space.

### Footer and chrome

- Bottom footer band now uses larger type, stronger contrast, more vertical padding, and a visible credit treatment so the project owner name and links remain legible.
- Intel header band received slightly stronger spacing and title treatment to better match the enlarged lower-panel footprint.

---

## v1.9.3 - 2026-03-22

Public-page layout and phone responsiveness

### Public pages

- Rebuilt the shared public-page design system around denser, asymmetrical layout rather than generic stacked SaaS cards.
- About page hero now uses a split layout with signal metrics, platform positioning, and a stronger editorial hierarchy.
- Public messaging now states more clearly that Phantom Tide is not a chatbot veneer over maritime data.

### Mobile

- Public navigation now shifts into explicit tap-target layouts before it becomes cramped.
- Hero actions collapse to full-width controls on smaller screens.
- Stat cards, signal bands, section headers, and footer layout now reorganize earlier for phones instead of relying on a single late stacking breakpoint.

### Delivery

- Frontend HTML cache policy now keys off response content type, so routes like `/about/` and `/docs/license/` receive `Cache-Control: no-store` rather than only the root document.

### Documentation

- Internal and public release markers were advanced to `v1.9.3`.

---

## v1.9.2 - 2026-03-22

Analyst UX, deploy freshness, documentation

### Frontend

- Intel briefings no longer rely on a binary hide or restore flow. The panel now keeps two live briefings visible by default, queues the rest, and lets analysts promote, queue, and reorder streams with persisted order.
- Added first-run onboarding, keyboard shortcut help, toast feedback, destructive-action confirmation, and compact-screen Layer and Detail drawers so the dashboard behaves more predictably on mobile and desktop.
- Empty states in detail and briefing surfaces now use explicit operator copy instead of leaving silent blanks.

### Platform delivery

- Frontend shell responses now send `Cache-Control: no-store`.
- Frontend JavaScript and CSS now send `Cache-Control: no-cache`.
- Rebuilt local app container verified to serve the new briefing queue markup and cache policy over `http://localhost`.

### Documentation

- Internal README bumped to `v1.9.2` and now links directly to the internal changelog.
- Internal roadmap current release and quality-track notes now reflect the briefing queue redesign and stale-bundle prevention work.

---

## v1.9.1 - 2026-03-22

Hotfixes

- Data collection was silently failing for several sources after a container privilege change introduced in `v1.9.0`. Reverted.
- Direct platform access was unavailable when the reverse proxy was not running. Restored for local use.
- Clicking an intel table row was closing the table instead of keeping it open and moving the map. Fixed.

---

## v1.9.0 - 2026-03-22

Public site, deployment hardening, documentation

- Public-facing site and legal notice refreshed.
- Build context hardened so credentials and secrets are not baked into images.
- Internal service credentials moved to environment-managed values.
- Reverse proxy configuration now adds standard security response headers and compression.
- Internal roadmap and documentation set were consolidated around the live codebase.
