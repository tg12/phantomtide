# Changelog

All notable changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

---

## v1.51.0 — 2026-04-08

### Faster steady-state refresh, stronger analyst workflow

This release improves the real browser hot path and makes several analyst-facing
surfaces more explicit and easier to trust.

#### Performance and map refresh

- High-frequency map and intel routes now support real browser revalidation
  with `ETag` / `304 Not Modified` on unchanged data. This reduces repeated
  full-body downloads and reparsing on steady-state refresh.
- Dense GeoJSON payloads were trimmed on the hot path so unchanged or low-value
  fields do not ride every refresh by default.
- The frontend refresh loop now uses bounded jitter and backoff under pressure
  instead of hammering the API in synchronized 30-second bursts.

#### Analyst workflow

- Convergence zones now expose a 72-hour change view. Cells can show prior
  score, score delta, and whether a hotspot is newly emerged versus 3 days ago.
- The geometry-anomalies analyst overlay is more usable: severity, raised
  geometry-test labels, and observed-window context are shown directly.
- The Area Intelligence Report now visibly anchors the queried radius on the
  map before building its plain-text SITREP, making the workflow easier to read.
- Tracked aircraft workflow and convergence scoring are now foregrounded more
  clearly in the product docs and About page so the platform's distinctive
  capabilities are easier to understand.

#### Trust and access

- API-key upgrade flow now distinguishes expired or disabled keys from generic
  invalid tokens.
- The starter onboarding `Skip` path now works correctly. Skipping no longer
  traps the browser in a gate-reopen loop on the next protected API request.

## v1.50.0 — 2026-04-07

### Production resilience and performance hardening

This release addresses silent failure modes, data loss vectors, and
performance bottlenecks identified during a comprehensive architecture audit.

#### Reliability

- **Health endpoint overhaul**: The `/api/health` endpoint now reports
  semantic system status (`ok` / `degraded` / `unhealthy`) based on data
  freshness of critical sources (AIS, OpenSky, live AIS, NOTAM, NGA
  warnings).  Previously, "ok" only meant the process was alive.  A new
  `degraded_reasons` field provides machine-readable diagnostics.
- **ClickHouse archival data loss detection**: The in-memory buffer that
  feeds ClickHouse writes now tracks overflow.  When buffer capacity is
  reached, the health endpoint reports the count of dropped events so
  operators can tune flush intervals or increase capacity.
- **Scheduler job resilience**: All scheduled background jobs now tolerate
  up to 2 minutes of scheduler backpressure before being classified as
  misfires.  Previously, a delay of more than 1 second caused silent job
  skips.
- **Reference data protection**: Collectors that return empty results due to
  upstream failures no longer wipe existing reference data (NOTAMs,
  navigation warnings, etc.).  The system retains the last known good
  snapshot until a successful collection replaces it.
- **Redis automatic reconnection**: If the Redis connection drops at
  runtime, the system now detects the failure and automatically reconnects
  on a cooldown schedule.  Previously, a Redis outage after startup
  permanently disabled event persistence until the next process restart.

#### Performance

- **VIIRS thermal baseline**: The per-cell statistical computation that
  scores thermal anomalies is now numpy-vectorized.  Large datasets
  (500k+ observations) process 10-50x faster, eliminating scheduler
  stalls during periodic baseline rebuilds.
- **Geospatial math consolidation**: Haversine distance calculations —
  previously duplicated across four modules with minor implementation
  differences — are consolidated into a single numpy-accelerated utility
  module (`core/geo_math`).  The VIIRS dark vessel proximity search now
  uses a single vectorized call over all candidate vessels instead of a
  per-vessel Python loop.

---

## v1.49.1 — 2026-04-07

### Supplemental air tracking data corrections

- **Zimbabwe government aircraft** (Z-WPF, Z-WPE): updated operator attribution.
  Robert Mugabe, who died in September 2019, is no longer referenced as president.
  Both aircraft are Boeing 767s operated by Air Zimbabwe and used on occasion as
  state transport under President Emmerson Mnangagwa (in office since November 2017).
- **Sudan government aircraft** (ST-PRA): attribution corrected.  Omar Al-Bashir
  was removed from power in April 2019 and faces outstanding ICC arrest warrants.
  The Ilyushin Il-62M itself was destroyed at Khartoum airport during the April
  2023 civil war and is no longer active.
- **Russia — Shuvalov-linked aircraft** (M-VQBI): title corrected.  The individual
  linked to this aircraft left the Russian government in May 2018 and now leads a
  state development corporation.
- **Belarus government aircraft** (EW-85815): status note added.  The Tupolev
  Tu-154M type was effectively retired globally by 2020–2021; operational status
  of this specific airframe is unconfirmed.
- **Qatar Amiri Flight** (VP-BAT): corrected.  The Boeing 747SP was retired from
  Qatar royal service around 2018–2019, subsequently re-registered as a US
  civil aircraft, and is listed for commercial sale.
- **NOAA Aircraft Operations Center fleet description**: updated to reflect the
  G-IV/SP phaseout.  The first replacement Gulfstream G550 entered service in
  spring 2025; a second arrives in 2028.  WP-3D Orion, Twin Otter, and King Air
  350CER fleet counts remain unchanged.
- **Bristow / HM Coastguard SAR network**: description updated to enumerate all
  10 permanent helicopter SAR bases and note two seasonal bases (Oban and Carlisle)
  activated in 2026 under the UKSAR2G programme.

---

## v1.49.0 — 2026-04-07

### GPS navigation signal interference layer

- A new **GPS interference grid** layer is now live, updated daily from
  aggregated aircraft receiver reports.  Affected cells are displayed as
  amber hexagons on the map.  Clicking a cell shows the percentage of
  aircraft reporting degradation and the observation date.
- Two severity tiers are tracked: **high** (≥50% of aircraft affected) and
  **medium** (25–49%).  Both feed the convergence scoring engine so a vessel
  dark event in a high-interference zone scores differently from one in a
  clear environment.
- Correlating a vessel going dark with an active high-interference grid cell
  at the same position and date helps distinguish GPS spoofing/jamming from
  a simple communications failure.

### HF/NAVTEX blackout indicator

- When NOAA SWPC data indicates HF radio blackout risk (Kp G3+ geomagnetic
  storm, or an M1.0+ X-ray solar flare, or an active ICAO space weather
  advisory), a derived **HF Blackout Zone** event is now generated.
- This covers the 2–30 MHz spectrum including NAVTEX, GMDSS distress, and
  MF/HF weather fax bands.  An active HF blackout means vessel distress
  calls on HF may not be receivable.
- Correlating a vessel comms gap with an active G3+ storm removes the
  jamming hypothesis and narrows the cause to atmospheric conditions.

### SATCOM constellation coverage (utility layer)

- Satellite visibility data for major commercial SATCOM constellations is
  now cached internally from public TLE sources, refreshed every 6 hours.
- This data underpins future vessel-level SATCOM coverage annotation: if
  the geometry shows zero satellites above the horizon at a vessel's
  position, a VSAT outage is explicable by coverage gap rather than
  interference.

---

## v1.46.0 — 2026-04-06

### Aircraft identity: FAA registry lookup

- Aircraft popups for US-registered aircraft (ICAO24 in the a00000–afffff
  range) now include a "Load registry data" button that fetches owner,
  N-number, manufacturer, model, year, type, seat count, weight class, and
  registration expiry from the FAA Releasable Aircraft Registry (305,709
  records, US public domain).
- Deregistered aircraft receive a prominent red "DEREGISTERED" badge.
- The popup header shows the registry build date so analysts know the data age.

### New source: NWS coastal marine warnings

- US coastal marine zone warnings (Gulf of Mexico, Atlantic, Pacific, Gulf
  of Alaska) are now collected from the National Weather Service and displayed
  as a dedicated layer.
- 13 maritime event types covered: Hurricane Force Wind Warning through Small
  Craft Advisory, filtered from the national alerts feed.
- Warnings feed into the convergence scoring engine with severity-weighted
  contribution (hurricane force = 2.5, storm warning = 2.0, down to 0.8 for
  small craft advisories).

### Area Intelligence Report

- Right-clicking the map now includes an "Area Report..." option that
  generates a structured plain-text SITREP for any radius.
- The report includes a signal summary by source, a notable signals table,
  nearby infrastructure, and entity feed hits — the same data shown in the
  proximity query panel, formatted for copy-paste into an analyst log.

### Bug fixes and reliability

- **VIIRS thermal and DNB markers now visible during daytime hours.** VIIRS
  satellite detections are collected 3–24 hours after the satellite pass.
  DNB (night-light) detections are from nighttime orbital passes and are
  structurally 6–18 hours old by observation time when viewed during the day.
  The time-window filter now uses data ingestion time rather than observation
  time, making all recent VIIRS data visible regardless of when the
  satellite passed.

- **OpenSky aircraft markers no longer flash/reset on page refresh.** Each
  aircraft is now identified by a stable ID derived from its ICAO24 address.
  Previously, IDs changed every 30 seconds as position timestamps rotated,
  causing every aircraft to appear to vanish and re-appear on each refresh.

- **VanIsle infrastructure data no longer fetches twice on startup.** A
  scheduler timing issue caused the infrastructure collector to run once at
  process start and once more immediately via its interval job. The interval
  is now correctly offset so the startup run is the only first fetch.

---

## v1.45.0 — 2026-04-06

### Bug fixes

- **Click-to-zoom on intel table rows fully restored.** Every table (aircraft,
  thermal hotspots, vessels, NOTAMs, GPS disruptions, MARAD, ICC, entity feed)
  had silently stopped jumping the map when rows were clicked. Root cause was
  a runtime crash in the marker interaction guard that occurred before the map
  focus call could fire. No data was affected; navigation and zoom functions
  now work correctly across all intel tables.

- **Clicking map markers overlaid by a convergence zone now works.** Previously,
  a convergence zone polygon's filled area blocked clicks on markers underneath it.
  The fix routes pointer events only through the zone border stroke, so markers
  inside a convergence area are fully interactive.

- **Tier upgrade now applies immediately.** Entering a premium access key
  previously left starter-capped data visible until the next timed refresh cycle.
  The upgrade now forces an immediate data refresh and clears the starter-tier
  badge from affected layers.

- **Sanctioned vessel popup cleaned up.** An informational note about upcoming
  premium depth expansion was shown unconditionally on all tiers. It has been
  removed as the expanded capability is now live.

### Email gate: now optional

- The first-visit email field is no longer required. Users can skip it by
  clicking "Skip" or by leaving the field empty and clicking "Continue."
  Non-empty fields are still validated and submitted. The modal text makes
  clear that email is optional and used only for maintenance notices.

### Supplemental Entity Feed — infrastructure overlay merged

- VanIsle Network infrastructure (ports, desalination plants, pipelines,
  refineries) is now part of the Supplemental Entity Feed layer. The
  previously separate toggle has been removed. One toggle controls both the
  entity corroboration rings and the infrastructure overlay.

### Compliance signals: AIS dark gap and vessel loitering (premium)

- Sanctioned vessel popups now show a red "AIS DARK GAP" badge or amber
  "LOITERING" badge when the vessel is independently flagged by the entity
  tracker for extended AIS silence or unusual loitering behavior.
- Convergence cell popups now label these signal families explicitly as
  "AIS dark gap (VanIsle)" and "Vessel loitering (VanIsle)" in their
  contributing evidence breakdown.
- The compliance signal feeds into the convergence scoring engine with
  weighting that reflects the significance of intentional AIS absence.

### Watchlist alert sidebar panel (premium)

- A persistent panel above "Recent NOTAMs" in the left sidebar lists every
  entity currently active in the entity feed that matches the vessel or
  aircraft watchlist.
- Each row shows an on-map status indicator (green dot = currently visible
  on the map), entity type, display name, watchlist database, and last-seen
  time.
- Clicking a row flies the map to the entity's last known position.
- The panel updates every refresh cycle. When no watchlisted entities are
  on-map, it shows a quiet empty state rather than hiding.

### Performance: frontend split

- The main JavaScript file has been split into three purpose-separated
  files loaded in dependency order. Parse time, maintainability, and
  parallel load behavior are improved. No user-visible functionality
  has changed.

---

## v1.44.0 — 2026-04-05

### Performance

- High-frequency map feed responses now carry conditional caching headers.
  Browsers that already hold the current data skip the payload download on
  repeat polls, reducing network and render overhead on stable pictures.
- Static reference layer responses are pre-built at startup rather than
  serialized on each request, removing per-request encoding cost from the
  most-polled routes.
- Watchlist entity feed calls are decoupled from the main 30-second refresh
  cycle. The feed refreshes on its own 10-minute cadence and no longer
  consumes shared request concurrency on every cycle.
- Container log writes switched to a lower-overhead driver, removing
  synchronous disk write pressure from every log line.

### SIGMET advisory popups

- SIGMET hazard popups now display plain-language descriptions rather than
  raw aviation codes. Hazard type, intensity, affected area, valid window,
  and movement are presented in readable form.
- Polygon hover labels upgraded to show region name and hazard type together
  instead of the raw code string.
- Original bulletin text preserved in a collapsible section for analysts who
  need the source record.

### Supplemental entity tracking layer (premium)

- New premium layer: cross-references a supplemental entity feed against live
  vessel and aircraft positions. Matched entities receive highlight rings on
  the map — red for watchlist hits, cyan for general corroboration.
- Watchlist hits appear in a dedicated intel table section showing entity
  type, identifier, observation count, last seen time, and live map status.
- Ring positions update each refresh cycle as underlying positions move, even
  when the entity feed itself has not changed.
- Available under the Supplemental Entity Feed toggle in the layer panel.

### Access tier gating

- Tier access control consolidated into a single registry. Adding a new gated
  feature now requires one entry rather than updates across multiple lists,
  eliminating the class of drift bug where a feature could appear in one list
  but not another.
- Fixed: three reference layers were accessible to starter-tier sessions
  despite being configured as premium-only. The registry consolidation
  corrected the inconsistency.
- Fixed: premium-tier unavailability badges were remaining visible for
  authenticated premium sessions due to a CSS specificity conflict between
  the badge class and the hidden attribute. Resolved.

---

## v1.43.0 — 2026-04-05

### Aviation weather — SIGMET layer

- International and domestic aviation weather SIGMETs integrated as a new
  map layer. Coverage includes convective activity, volcanic ash, turbulence,
  tropical cyclone warnings, and other hazards relevant to maritime airspace.
- Hazard polygons rendered as semi-transparent overlays with centroid markers.
  Each event shows hazard type, severity, affected area, altitude ceiling, and
  valid window.
- A maritime relevance flag distinguishes hazards directly over ocean areas
  from land-based events.
- Layer refreshes every 20 minutes. Expired events are dropped before display.

### Vessel and aircraft track history (premium)

- Vessel and aircraft detail panels now include a Show Track button for
  premium sessions. Selecting it renders a fading historical track polyline
  — opacity scaled from oldest to newest — with per-segment timestamps and
  speed.
- Track history draws from the platform archive rather than the live
  position feed, so coverage extends back through the retention window.
- Starter sessions receive an empty track response with a clear tier
  indicator rather than an error.

### New maritime reference layers (premium)

- Three additional maritime reference overlays added to the premium layer set:
  - **Restricted and danger zones** — areas where vessel presence requires
    explanation. AIS gaps inside these zones are expected rather than
    anomalous.
  - **Ship-to-ship transfer zones** — lightering areas where vessels may
    legally conduct at-sea transfers. Sanctioned-vessel dwell in these areas
    is a potential illicit transfer signal.
  - **Designated anchorages** — official holding areas. Vessels anchored
    outside designated anchorages represent a deviation from expected
    behaviour.

### Entity feed integration

- Supplemental vessel and aircraft identity feeds integrated as a background
  data source, refreshing every 10 minutes independently of the main refresh
  cycle.
- Entity feed corroboration badges appear in vessel and aircraft detail panels
  when the identifier is present in the feed, showing observation count and
  last seen time.
- Proximity query results include an entity feed corroboration column for
  matched vessels and aircraft within the search radius.
- Watchlist-matched entities in the feed trigger hypothesis entries when
  active positions are present.

### Bug fix

- Ports and Terminals sidebar badge corrected from premium to enterprise
  following the tier change in v1.42.0.

---

## v1.42.0 — 2026-04-05

### Ports and Terminals moved to enterprise tier

- The global ports and terminals reference layer is now enterprise-only.
  The layer is renamed from Ports to Ports and Terminals across all
  user-facing surfaces. The data and underlying access path are unchanged.
- Locked sessions now see explicit enterprise-tier messaging rather than
  the generic premium-locked copy.

### Hypothesis expiry

- Analyst hypotheses now expire after 48 hours on each collection cycle,
  keeping the hypothesis panel uncluttered in long-running deployments.
  The hypothesis query endpoint accepts an optional age filter for
  on-demand trimming independent of the scheduled expiry.

### Intel table hardening

- Navigation warning, broadcast warning, and NOTAM intel table routes
  hardened against silent failures on records with missing or null fields.
  Count queries use direct store methods rather than over-fetching and
  slicing in the application layer.

---

## v1.41.1 — 2026-04-04

### Ports layer and thermal AOI triage

- Global ports reference layer added at premium tier with startup fallback
  seeding so the layer survives volume-backed deployments.
- Thermal proximity alerts can now surface port context alongside energy,
  datacenter, and strategic infrastructure context.
- Thermal alert detail panels now distinguish proxy-only detections from
  confirmed anomalies and show observation age more clearly.

---

## v1.41.0 — 2026-04-04

### Thermal intelligence and operational truthfulness

- Offshore drilling unit state now normalised at ingest. Status, activity
  bucket, and detail fields arrive pre-computed rather than being inferred
  from raw strings in the browser.
- Thermal detection subtype fidelity made explicit. When the feed cannot
  distinguish fire subtype, collector health degrades visibly rather than
  silently implying the feed is inactive.
- Thermal layer counts now separately report loaded, rendered,
  maritime-filter-held, and zoom-held state, removing the common confusion
  where a maritime filter made a live feed appear empty.

---

## v1.40.0 — 2026-04-04

### Mobile — first-class support

- Fixed white-screen regression on mobile marker tap. The detail panel
  backdrop is now a dark semi-transparent overlay rather than a near-opaque
  white cover.
- Fixed API unavailable state on iOS Safari caused by the onboarding dialog
  being pushed behind the software keyboard. Dialog now tracks the visual
  viewport so the submit control is always reachable.
- Desktop sidebar density reduced: touch-sized controls scaled down for
  pointer use without affecting mobile touch targets.
- Removed obsolete CSS properties with no effect on current browsers.
- Added viewport safe-area support for notched and Dynamic Island devices.

---

## v1.39.0 — 2026-04-03

### Thermal triage and operator context

- Maritime thermal subfilter added to the VIIRS layer, allowing isolation of
  offshore detections from land-based fire activity.
- Thermal detections now carry an explicit policy outcome —
  background, context, watch, or page — so the system's assessment is visible
  rather than implicit.
- Known offshore flare basins encoded as negative controls so routine
  hydrocarbon signatures are not promoted based on proximity alone.
- Thermal popup and proximity surfaces now distinguish offshore and
  gas-flare detections and show nearby infrastructure context.

### Persistence and refresh discipline

- Platform persistence health now visible end-to-end from backend to
  dashboard.
- Partial persistence flush failures now requeue buffered events rather than
  discarding them.
- Hidden layers no longer continue refreshing when not in view.
- Large event snapshots no longer rewrite browser session storage on every
  poll when data has not changed.

---

## v1.38.1 — 2026-04-03

### UX tightening

- Redundant manual refresh controls removed. The dashboard now exposes the
  automatic refresh loop through a passive countdown rather than duplicate
  operator controls.
- Unused sidebar search UI removed.
- Access tier banner can now be dismissed per session.
- Premium expanded-depth toggles now unlock correctly on premium sessions
  and allow explicit fallback to preview depth.

---

## v1.38.0 — 2026-04-02

### Performance and serve-path hardening

- Map polling reuses cached responses until data actually changes rather than
  expiring on a wall-clock TTL, so unchanged layers stop missing the cache on
  routine refresh cycles.
- Sanctioned-vessel route and zone index rebuilt only when the underlying
  source has changed.

### Access and onboarding

- Protected browser sessions now require server-issued onboarding completion
  before the API unlocks. Onboarding responses marked no-store to prevent
  stale session state being cached by the browser.
- Onboarding intake rejects obvious placeholder addresses and enforces
  uniqueness.

---

## v1.37.0 — 2026-04-02

### Thermal intelligence

- Thermal layer now separates fire detections from night-light detections,
  exposes hotspot clusters with unusualness scoring, and renders pixel-footprint
  geometry where available.
- Nearby port, offshore, infrastructure, and strategic context surfaces in
  thermal proximity alerts.
- Dense thermal layers now explain loaded versus rendered state through counts,
  zoom hints, and subfilter breakdowns.

### Performance and startup

- Thermal proximity route no longer materialises full event payloads on hot
  paths, removing the serialisation cliff under repeat load.
- Large static reference layers cached server-side and restored from saved
  state through a staggered idle queue rather than a fan-out load at startup.

### Persistence

- Event geometry now persists correctly through the archive and restores on
  read, closing a silent geometry-loss path for geometric evidence types.
- Source health auto-expands when sources are degraded or cache-backed.

---

## v1.36.0 — 2026-04-02

### Access and session upgrades

- Starter access upgrades cleanly through browser session exchange when a
  valid key is entered. The access-key store is shared between the management
  tooling and the running container.
- Header now surfaces an explicit access key entry point. Sidebar no longer
  duplicates the upgrade prompt.

---

## v1.35.0 — 2026-04-02

### Access gate

- Starter access now gates on a first-use modal before the dashboard starts,
  rather than treating onboarding as a cosmetic overlay.
- Email intake stays on-box in runtime-only storage with no public route
  exposure.
- Starter-tier limits now apply consistently across both the map feed and
  the raw event API.

---

## v1.34.0 — 2026-04-02

### Access state truthfulness

- Frontend access state now follows server truth on session expiry, logout,
  or tier downgrade. Stale privileged data is cleared when the backend narrows
  access.
- Optional-auth deployments fall back cleanly to starter access on logout
  rather than freezing the dashboard.
- Access panel now shows current tier, session status, and expiry.

### Performance

- GeoJSON cache hits reuse pre-serialised bytes. Capped map responses keep
  newest-first semantics without sorting the full result set.

---

## v1.33.0 — 2026-04-01

### GeoJSON CPU outage — fix

- Bulk map feed responses no longer force maritime enrichment by default.
  The enrichment index rebuilds on source file change rather than a
  fixed timer. Large feature sets skip analyst-facing enrichment instead of
  turning the default map feed into a CPU trap.

See [geojson-cpu-outage.md](docs/geojson-cpu-outage.md) for the full incident record.

---

## v1.32.0 — 2026-04-01

### Intelligence and analyst UX

- VIIRS proximity alerting restored for close-range offshore detections near
  strategic context.
- Nearest cable distance suppressed from detail panels when the nearest cable
  is more than 1000 km away.
- Starter-tier preview layers render in a visibly distinct state. Upgrade
  messaging uses generic access language rather than source-specific wording.

---

## v1.31.0 — 2026-04-01

### Access control

- Optional dashboard authentication added as a deployment-wide session gate.
  Protected deployments require a browser session exchange before API access
  is granted. Open local development can remain ungated by configuration.
- Starter tier defaults to a reduced map profile. Dense premium-candidate
  layers are off by default. Premium depth is capped until a session upgrade
  is completed.
- Military installation data made internal-only. User-facing routes and
  frontend load paths removed.

### Source health

- Collector health states preserve backend run modes end-to-end. The UI can
  now distinguish empty, error, cache, stale, and partial states rather than
  collapsing them into ambiguous badges.

---

## v1.30.0 — 2026-04-01

### Archive and evidence fidelity

- First archive boundary: raw feed data archived before normalisation so
  replay and provenance work has a stable baseline to work from.
- Release version exposed through a runtime API endpoint so the dashboard
  header version reflects the deployed line rather than hardcoded text.

### Performance

- Convergence endpoint uses a short-lived response cache, removing redundant
  recomputation from the default dashboard poll loop.
- Refresh fan-out split by cadence: slow-moving sources no longer refetch on
  every 30-second cycle.

---

## v1.29.0 — rolled back

This candidate was rolled back. Changes were carried forward into v1.30.0.
