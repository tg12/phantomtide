# Changelog

All notable changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

---

## v1.8.1 — 2026-03-21

**Hotfix**

- Fixed a JavaScript strict-mode parse error in the detail panel that silently prevented the entire frontend from loading. Symptom: map tiles rendered, status showed "Awaiting data", no API calls were made.

---

## v1.8.0 — 2026-03-21

**Map feel, performance, and bitemporal time**

This release addressed three independent concerns that had accumulated: the map felt physically wrong to navigate at speed; the 30-second refresh cycle was doing expensive work for events that had not changed; and time semantics were ambiguous — a single timestamp field was carrying observation time, ingestion time, and expiry simultaneously.

**Map sensitivity**
- Scroll wheel zoom is less aggressive — accumulates ticks before committing, requires more movement per level
- Zoom snaps to half-integer levels only, eliminating fractional micro-positions
- Pan inertia deceleration and max speed tuned for a snappier, less drifty feel
- Zoom animation easing curve steepened for a smoother subjective feel

**Performance**
- SVG marker icons are now memoised — approximately 36 shape/colour/size combinations exist in practice; after the first render cycle all icon lookups are O(1) memory reads instead of string concatenation
- Marker fast-path: colour is computed first and compared; if an existing marker has not changed colour, no SVG or popup HTML is rebuilt
- Search filter debounced at 120ms to prevent full marker scans on every keystroke
- Risk zone recompute debounced at 200ms on zoom so rapid scroll does not trigger repeated O(N²) grid rebuilds
- Pending refresh flag: a refresh blocked by an active pan/zoom is queued and fires 250ms after the interaction ends rather than being silently dropped

**Bitemporal time**
- Every event now carries `collected_at` (when this system ingested it) separate from `timestamp` (when the phenomenon was observed)
- `valid_until` field added for events with a known expiry: active notices, nav warnings, advisories
- Time window filter now respects `valid_until` — an event with a future expiry date is never hidden by the 6-hour or 24-hour window
- Event detail panel shows a time provenance bar: `obs: Xh ago`, `rcv: Xm ago` when meaningfully different, and an expiry badge (EXPIRED / expires Xm / valid Xh)

---

## v1.7.0 — 2026-03-21

**Multi-coordinate geometry and shape rendering**

Events from text-based sources now render their full spatial footprint rather than a single centroid point. All coordinate formats found in maritime source text are extracted and the correct geometry type is chosen: polygon for area descriptions, linestring for routes and cables, circle for exclusion zones.

- Exercise areas and restricted zones render as filled polygons
- Multi-point warnings render as polygons or linestrings depending on point count
- All geometry overlays respond to layer checkboxes — toggling a source hides both point markers and shape overlays
- Clicking any geometry overlay opens the same detail panel as the marker anchor
- Weather mesh fix: daily wave/weather averages bypass the time-window filter — these are reference data, not streaming positions; the filter was incorrectly hiding them at narrow time windows

---

## v1.6.0 — 2026-03-21

**Ocean state layer, operational platform clusters, wind overlay**

- Delaunay triangulation replaces the previous connection-line approach for the weather mesh. Sensor observations are triangulated into a continuous field; triangle opacity encodes sensor density and data confidence
- Severe sea states pulse with a slow animation
- Wind direction arrows placed at each station; size scales with wind speed
- Operational platform clusters: drilling unit positions are grouped by proximity into field polygons. Active fields are teal. Fields with removed units are amber
- Ocean state legend redesigned with wave-height ranges, opacity explanation, wind arrow indicator, and cluster status legend
- Platform position history retained for 90 days in a rolling log file

---

## v1.5.0 — 2026-03-21

**Interface overhaul, universal time formatting, table navigation**

- Universal timestamp formatter wired across all popup types and table cells — one toggle switches all times between relative ("2h ago") and absolute UTC
- WCAG accessibility improvements: focus rings, font size floors, ARIA landmarks, proper button tap targets
- Intel table row click flies the map to the event location across all three table types
- Front-end dependencies vendored locally — no CDN dependency

---

## v1.0.0 — 2026-03-20

**Initial release**

Live maritime intelligence dashboard. Nine independent data pipelines feeding a dark global map with 30-second refresh.

Core architecture:
- Reference store for stable-ID sources using atomic snapshot replacement — cancelled warnings disappear automatically
- Ring buffer for streaming sources with configurable eviction
- Hot cache with long-term persistence backend
- File cache fallback for all reference sources — platform shows data before the first live collection cycle on restart
- Rule engine with dark fleet detection, airspace risk, and nav warning proximity rules
- Docker Compose stack, health monitoring endpoint, per-source staleness tracking
