# Changelog

All notable changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

---

## v1.9.1 — 2026-03-22

**Hotfixes**

- Data collection was silently failing for several sources after a container privilege change introduced in v1.9.0. Affected sources produced no new events despite reporting healthy status. Reverted.
- Direct platform access was unavailable when the reverse proxy was not running. Restored for local use.
- Clicking a row in any intel table was closing the table instead of keeping it open, and the map was not navigating to the selected item. Fixed. Tables now remain open and the map pans to the item correctly.

---

## v1.9.0 — 2026-03-22

**Public site, deployment hardening, documentation**

### Public site

- Design system rewritten. Flat dark palette, structured card borders, square controls, monospace footer. Removed visual patterns that dated the interface.
- About page: social sharing metadata added. Above-the-fold call-to-action added.
- Legal notice: complete rewrite. See [Legal Notice](/docs/license/).

### Deployment

- Build context hardened: credentials and secrets are no longer included in container images under any path.
- Credentials for internal services are now environment-managed with no hardcoded defaults.
- Container images pinned to specific versions; no floating tags.
- Reverse proxy configuration adds standard security response headers and compression.
- First-run script auto-generates strong random credentials for internal services. Idempotent on subsequent runs.

### Documentation

- Roadmap consolidated. Session notes removed; forward-looking content preserved.
- Stale internal documents deleted.

---

## v1.8.2 — 2026-03-21

**Collector restore**

Two data collectors were failing silently on every cycle due to a runtime incompatibility in the shared text enrichment layer. The exception guard was too narrow and did not catch the error variant raised in this environment. Both collectors now run cleanly on every cycle.

---

## v1.8.1 — 2026-03-21

**Hotfix**

- Fixed a frontend parse error that silently prevented the dashboard from loading. Symptom: map tiles visible, no data, no API calls initiated.

---

## v1.8.0 — 2026-03-21

**Map feel, performance, bitemporal time**

Map navigation:
- Scroll wheel zoom accumulates ticks before committing — less accidental zoom
- Zoom locks to half-integer steps, eliminating fractional micro-positions
- Pan inertia and deceleration tuned for a snappier, less drifty feel

Performance:
- Marker icons memoised — first render cycle builds the cache; subsequent renders are O(1) lookups
- Marker fast-path: if colour has not changed, no SVG or popup HTML is rebuilt
- Search filter debounced to prevent full scans on every keystroke
- Risk zone recompute debounced on zoom to prevent repeated full rebuilds during scroll
- Blocked refresh queues and fires after interaction ends rather than being dropped

Time semantics:
- Events now carry three separate time fields: when the phenomenon was observed, when the platform ingested it, and when it expires
- Time window filter respects expiry — events with a future expiry are never hidden
- Detail panel shows a time provenance bar and expiry badge

---

## v1.7.0 — 2026-03-21

**Geometry and shape rendering**

Events from text-based sources now render their full spatial footprint rather than a single point. Coordinate formats are extracted from source text and the correct geometry type is selected automatically: polygon for area descriptions, linestring for routes and cables, circle for exclusion zones.

- Geometry overlays respond to layer toggles
- Clicking any shape overlay opens the detail panel
- Weather data bypasses the time-window filter — it is reference data, not a streaming position feed

---

## v1.6.0 — 2026-03-21

**Ocean state layer, platform clusters, wind overlay**

- Delaunay triangulation produces a continuous ocean state field from sparse sensor observations. Triangle opacity encodes data confidence — dense coverage is opaque, sparse coverage fades out.
- Severe sea states pulse
- Wind direction arrows scaled by speed at each station
- Drilling unit positions grouped by proximity into field polygons. Active fields distinguished from fields with removed units.
- Platform position history retained for 90 days

---

## v1.5.0 — 2026-03-21

**Interface, time formatting, table navigation**

- Universal timestamp formatter across all popup types and table cells. Single toggle switches between relative and absolute UTC display everywhere.
- Accessibility: focus rings, font size floors, ARIA landmarks, button tap targets
- Intel table row click navigates the map to the event location
- All frontend dependencies vendored — no external CDN dependency

---

## v1.0.0 — 2026-03-20

**Initial release**

Live maritime and airspace intelligence dashboard. Multiple independent data pipelines feeding a dark global map with 30-second refresh.

- Reference store with atomic snapshot replacement — cancelled warnings disappear automatically
- Ring buffer for streaming sources with configurable eviction
- Hot cache with persistence backend
- File cache fallback — platform shows data on restart before the first collection cycle completes
- Cross-source rule engine
- Docker Compose stack, health monitoring, per-source staleness tracking
