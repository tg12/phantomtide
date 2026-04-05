# Changelog

All notable changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

---

## [Unreleased] — v1.45.0

- Watchlist alert panel: sidebar listing of all on-map entities matched by
  vessel and aircraft watchlists, sortable by last seen, with entity feed
  corroboration badges where available.

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
