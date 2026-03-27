# Changelog

All notable changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

---

## v1.16.2 — 2026-03-27

**Strategic infrastructure overlay and infrastructure-aware thermal alerts**

- Added a strategic infrastructure overlay that combines cables, landing
  stations, pipelines, converter nodes, data-gravity sites, energy buffers,
  space ground-segment sites, and selected industrial chokepoints into one
  map layer.
- Fixed infrastructure marker rendering so data centers, energy facilities,
  and strategic overlay points now appear reliably on the map instead of
  silently disappearing on schema mismatches.
- Thermal anomaly alerts now evaluate nearby infrastructure context more
  broadly, including eligible strategic nodes in addition to energy
  facilities, data centers, and military reference points.
- Improved click-through workflow from thermal alerts into the relevant map
  context layer.
- Added internal render diagnostics for static infrastructure layers to speed
  troubleshooting when a reference layer appears empty.

---

## v1.16.1 — 2026-03-27

**Infrastructure layer rendering, icon system overhaul, and data source reliability**

This patch release resolves a set of silent rendering failures that were
preventing critical infrastructure layers from appearing on the map, and
ships a complete icon differentiation pass across all overlay types.

- **Nuclear and energy infrastructure markers were not rendering.** The global
  power plant dataset was loading correctly at the collector level but a
  frontend symbol resolution path was falling back silently to a null icon,
  resulting in markers that were present in the data but invisible on the map.
  Fixed. Nuclear plants, conventional power stations, and associated energy
  facilities now render with their correct symbols at all zoom levels.

- **Data center layer was not populating.** The coastal datacenter reference
  set used by the VIIRS thermal proximity alert was ingesting cleanly but the
  map layer toggle was bound to a stale key following the v1.16.0 store
  routing refactor. Markers were allocated but never dispatched to the render
  pipeline. Fixed. Data centers now appear correctly when the layer is enabled,
  and the VIIRS proximity alert now has the full facility set available for
  proximity evaluation.

- **Icon system redesigned across all overlay types.** With seventeen source
  layers now active simultaneously, earlier icon choices were producing visual
  collisions — different source types were using shapes and colours that were
  too close to distinguish at a glance, particularly between satellite
  detections, infrastructure reference points, and advisory anchors. Each
  overlay type now carries a distinct symbol vocabulary:
  - Satellite detections (SAR and imaging passes) use angular, radar-style
    diamond markers in cool blue-white
  - Energy and nuclear infrastructure uses a bold hexagon in amber
  - Data centers use a square grid marker in steel blue
  - NOTAM airspace zones retain their magenta ring with directional indicator
  - Convergence cells remain the scored heat-gradient polygons
  - Earthquake events retain scaled violet stars
  - Watchlist aircraft retain pulsating red glow
  - Military installations retain red star markers
  - Seized and Iran Navy vessels retain orange anchor and red star respectively
  The goal is that any two active layers should be immediately distinguishable
  without reading a label.

- **VIIRS thermal proximity banner now references the correct facility
  inventory.** Previously the banner could report zero nearby facilities even
  when data center and nuclear markers were in range, because the proximity
  check was running against an incomplete snapshot. Now correctly references
  the full rendered facility set.

---

## v1.16.0 — 2026-03-27

**Seismic and weather intelligence layers, EMODnet infrastructure overlay,
nuclear plant reference layer, and VIIRS thermal proximity alert**

This release adds two new live data sources, a European infrastructure overlay,
a nuclear facilities reference layer, and a real-time thermal anomaly alert
system.

- **USGS earthquake feed** now live. Magnitude 2.5 and above worldwide, updated
  every 15 minutes. Events appear as violet star markers scaled by magnitude (
  small for below M5, medium for M5–6.5, large for M6.5+). Each popup shows
  magnitude, depth, place, tsunami flag, PAGER alert level, and a direct link
  to the USGS event page. Significant earthquakes (M5.5+) contribute to the
  convergence score for nearby maritime cells — undersea quakes are direct
  context for cable cuts, tsunami advisories, and acoustic propagation
  affecting sonar-dependent vessels.

- **Environment Canada marine weather warnings** now live. 30-minute updates
  covering the Gulf of St Lawrence, Hudson Bay, and the Canadian Arctic —
  waters not served by NDBC. Storm and hurricane warnings weight the
  convergence score at 2×; gale and freezing spray warnings at 1.5×. Fills the
  northern Atlantic intelligence gap that affects Russia's shadow fleet routes
  and Arctic shipping corridors.

- **EMODnet Human Activities overlay** added as a toggleable map layer for
  European waters. Covers submarine cables, oil and gas pipelines, and offshore
  wind farm polygons. No backend required — tiles are served directly from
  EMODnet's public WMS endpoint. Toggle is in the map controls panel.

- **Nuclear facilities reference layer** added. Approximately 250 nuclear power
  plants worldwide filtered from a global power plant dataset, rendered as
  toggleable reference markers. Clearly labelled as static reference data, not
  live monitoring.

- **VIIRS thermal proximity alert** added. When a satellite thermal detection
  (VIIRS fire or night-time light anomaly) falls within 25 km of a nuclear
  plant, coastal datacenter, or military base in the last 5 minutes, an orange
  alert banner appears at the top of the map. The banner shows the number of
  detections, the nearest facility name and distance, and links directly to the
  thermal event on the map. Updates on every refresh cycle.

- Three data pipeline bugs fixed: NERACOOS collector was crashing silently on
  every run due to an unexpected keyword argument, causing the Gulf of Maine
  mooring layer to always fall back to cache. USGS and ECCC event counts were
  showing as zero in the source health panel due to a misconfigured store
  routing table. All three sources now report correctly.

---

## v1.15.0 — 2026-03-27

**Watchlist intelligence, sanctioned fleet layer, and infrastructure hardening**

This release ships the aircraft and vessel watchlist layer, the sanctioned fleet
frontend, the maritime risk zone overlay, and infrastructure updates to the Docker
stack.

- Live aircraft positions are now cross-referenced against a 16,000-entry ICAO hex
  registry covering military, government, police, coastguard, medevac, and other
  tracked categories. Matched aircraft render with a pulsating red glow marker and
  are distinguishable from ordinary air traffic at a glance.
- A homepage alert banner appears when any tracked aircraft are currently visible,
  showing count and registration / category. Updates on every refresh cycle.
- AIS vessel positions cross-referenced against 92 PLAN/CCG fleet MMSIs and 12
  notable yacht MMSIs at ingest.
- Military installation static reference layer available in the map controls: 647
  geocoded bases rendered as red-star markers on toggle.
- New analyst endpoint `/api/intel/aircraft-alerts` returns all currently spotted
  watchlist aircraft with registration, operator, category, and position.
- Sanctioned vessel fleet map layer live. FleetLeaks vessels with a spoofing score
  of 2 or higher display a distinct alert icon; score 1 shows a dashed border.
  Per-vessel popup includes IMO, type, flag, AIS status, sanctioner breakdown, and
  spoofing score with per-agency sanction dates.
- TankerTrackers maritime risk zone overlay: 183 named polygon zones rendered as a
  toggleable layer. Zone name appears on hover.
- Seized vessel and Iran Navy registry rendered as a distinct map layer: orange
  anchor icon for seized tankers, red star for Iran Navy and IRGC assets.
- Docker stack updated: ClickHouse confirmed on latest stable GA release
  (v26.2.5.45-stable, multi-arch). MinIO pinned to final CVE-patched release
  following repository archive.
- Backend scheduler refactored to a table-driven registration pattern. Startup
  preload registry unified. All slow reference collectors now share one wrapper.

---

## v1.14.0-dev — 2026-03-26

**Aircraft watchlist intelligence layer**

- Live aircraft positions from OpenSky are now cross-referenced against a
  16,000-entry ICAO hex registry of tracked aircraft at the moment they are
  ingested. Matched aircraft include military, government, police, coastguard,
  medevac, and other operationally relevant categories.
- Matched aircraft render on the map with a pulsating red glow marker so
  they are immediately distinguishable from ordinary air traffic.
- A homepage alert banner appears when any tracked aircraft are currently
  spotted, showing how many and which registrations / categories they belong
  to. The banner updates on every refresh cycle.
- AIS vessel positions are now cross-referenced against a registry of 92
  People's Liberation Army Navy and China Coast Guard vessels plus 12
  notable yachts by MMSI.
- A static military installation layer is now available in the map controls.
  647 geocoded bases can be toggled on as red-star markers. The layer loads
  on first enable and does not affect the normal refresh cycle.
- New analyst endpoint `/api/intel/aircraft-alerts` returns all currently
  spotted watchlist aircraft with registration, operator, category, and
  position details.

---

## v1.13.0 — 2026-03-26

**Frontend layer rollout, NERACOOS oceanographic moorings, and scheduler hardening**

- Sanctioned vessel fleet map layer now live. FleetLeaks vessels with a spoofing
  score of 1 or higher display with a dashed red border indicator; score 2 or 3
  draws a distinct alert icon. Layer toggle and per-vessel detail popup included.
- TankerTrackers maritime risk zones overlay now rendered on the map. Toggle in
  the layer control shows or hides the 183 named polygon zones. Zones load
  independently of the event refresh cycle.
- Seized vessel and Iran Navy registry now appears as a distinct map layer. Seized
  vessels and Iran Navy vessels render with separate icon styles and popup detail.
- NERACOOS ERDDAP oceanographic moorings integrated. Six Gulf of Maine fixed
  mooring stations (air temperature, wind, wave height, wave period, sea surface
  temperature, salinity, pressure) collected at 60-minute intervals with no
  authentication required. Stations: A01, B01, E01, M01, N01 met and wave arrays.
- Backend scheduler refactored. All slow-polling reference collectors now share a
  single wrapper function and a table-driven registration pattern. Adding a new
  reference source requires one registry entry rather than a bespoke function.
- Startup preload registry unified on the same pattern — eight sources now use
  the common loader rather than eight identical functions.
- Source colors, shapes, and staleness thresholds wired for FleetLeaks,
  TankerTrackers seized, and NERACOOS in the frontend constant tables.

---

## v1.12.0 — 2026-03-26

**Sanctioned fleet intelligence layer**

- Four new data sources integrated covering sanctioned vessel tracking, maritime
  risk zone context, and seized vessel monitoring.
- Live AIS positions are now collected for known sanctioned vessels alongside
  spoofing anomaly signals: whole-degree position rounding, impossible speed for
  vessel type, and missing heading data. Each vessel carries a spoofing score
  from 0 to 3 derived from these flags.
- Sanctions cross-reference data from multiple agencies (OFAC, EU, UK FCDO,
  Canada, Switzerland, Australia, UN) merged into vessel records by IMO number
  at collection time.
- 183 named maritime risk zone polygons integrated covering chokepoints, conflict
  zones, and high-risk transit corridors.
- Seized and Iran Navy vessel registry integrated with last known position data.
- New API endpoints expose sanctioned vessel lists with filters (vessel type,
  spoofing score, sanctioning agency), maritime risk zone polygons, and the
  sanctions registry by IMO.
- Frontend map layer for sanctioned vessels is in the next release.

---

## v1.11.0 — 2026-03-26

**Data freshness and source reliability**

- GPS disruption events now reflect their actual report date rather than the
  collection time. Previously, all GUIDE events appeared with the same timestamp;
  they now carry the date the disruption was first reported to NAVCEN.
- Coordinate extraction improved across all text-based sources. Three additional
  formats are now recognized, including labeled lat/lon pairs and signed decimal
  coordinates. Sources that previously placed events at 0,0 due to unrecognized
  coordinate notation now resolve correctly.
- Datetime parsing hardened against non-standard concatenated date-time strings
  used in certain official maritime data feeds.
- Provenance and confidence metadata extended to two additional sources, giving
  the analyst layer more signal on which position and timestamp fields are
  authoritative versus inferred.
- Convergence scoring and rule evaluation now use a consistent datetime parser
  across all comparison paths, eliminating a class of silent mismatches.
- Several resilience improvements to collectors that face upstream WAF
  protection, including retry logic and structured fallback logging.

---

## v1.10.1 - 2026-03-24

**Intel table reliability and data freshness**

- Fixed intel table refresh behavior: analyst tables now update consistently regardless of panel visibility, eliminating stale data when reopening briefing panels.
- Enhanced event sorting to ensure newest items appear at the top of all intel tables.
- Maintained full backward compatibility with existing API consumers while improving data consistency.

---

## v1.10.0 - 2026-03-23

**ICC-CCS live piracy, convergence zones, and map clarity**

- Added ICC-CCS IMB live piracy incidents as a first-class source, including a dedicated analyst table and map layer.
- Shipped the first convergence release: Phantom Tide now scores multi-source overlap by map cell and renders those cells directly on the dashboard.
- The dashboard now tells the operator when convergence cells are being hidden by zoom level instead of leaving the overlay ambiguous.
- When every source layer is enabled, the interface now warns that the map is in its noisiest state.
- Dense global layers received another performance pass so overview use is less expensive when multiple feeds are shown together.
- Access handling now degrades more cleanly when the edge cannot recover a public client IP. Legitimate users who previously hit false "Non-Public IP Address Detected" blocks now get a short manual verification step instead of an immediate hard failure, and that prompt data is not retained.

## v1.9.5 - 2026-03-23

**MARAD, source trust visibility, and release-sync cleanup**

- Added MARAD MSCI advisories to the live platform surface, including a dedicated analyst table and map layer for regional U.S. maritime threat notices.
- Source health now distinguishes between live, cache-backed, and failed states for slower reference collectors so degraded sources are visible instead of silently reading healthy.
- Public-feed collectors now use stronger browser-like request headers, reducing avoidable upstream blocking on HTML and RSS fetches.
- Public documentation is now explicitly aligned with the shipped internal release so the docs repo and application release marker stay in step.

---

## v1.9.4 — 2026-03-22

**Intel panel layout and footer visibility**

- The intel strip now keeps a clearer two-panel layout on wider screens, with active briefing cards using more of the available lower-page space.
- Footer links and attribution were enlarged and given stronger contrast so platform ownership and navigation remain legible.

---

## v1.9.3 — 2026-03-22

**Public page design and phone layout**

- Public pages now use a denser, less generic layout with a split hero, signal framing, and stronger editorial hierarchy.
- About page copy now makes clearer that Phantom Tide is not a chatbot layer over maritime data.
- Mobile layout for public pages now reorganizes earlier with clearer tap targets and full-width actions on smaller screens.
- Static HTML routes now revalidate more reliably, reducing the chance of stale public pages after a rebuild.

---

## v1.9.2 — 2026-03-22

**Analyst workflow and documentation**

- Intel briefings now default to a calmer two-stream queue instead of a binary
  hide or restore flow. Analysts can promote and reorder streams without losing
  context.
- Onboarding, keyboard shortcuts, confirmation dialogs, toast feedback, and
  improved empty states make the platform's interaction model clearer on both
  desktop and compact screens.
- Frontend cache headers were tightened so rebuilt deployments are less likely
  to leave users on stale dashboard bundles.
- Public and internal README files now separate shipped capabilities from
  roadmap items and reflect the current analyst workflow more accurately.

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
