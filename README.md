# Phantom Tide

**Cross-domain maritime intelligence from open signals, not headlines**

> The useful signal is usually not the dot on the map. It is the gap between
> what is being broadcast and what the rest of the environment says is true.

---

Phantom Tide is a maritime and airspace OSINT platform built around that idea.
It does not treat AIS, notices, weather, aircraft, or satellite detections as
separate products. It evaluates them together through geospatial-intelligence
workflows focused on timing, geometry, proximity, and contradiction.

The result is a working picture that answers three questions quickly:

1. Where is the most interesting contradiction right now?
2. Which sources agree, and which ones do not?
3. How much confidence should an analyst place in that signal?

Current release: **v1.39.0**

Next tracked release: **v1.40.0** (planning)

The current release makes offshore thermal detections easier to interpret,
reduces avoidable background refresh churn, and exposes runtime health more
honestly when persistence is degraded.

Live: [phantom.labs.jamessawyer.co.uk](https://phantom.labs.jamessawyer.co.uk)

---

![Phantom Tide — full dashboard overview](docs/screenshots/overview.png)
*Global overview. The point is not that many things are happening. The point is
which things should not be happening together.*

---

## What It Does Today

Phantom Tide currently combines live, periodic, and reference layers across
surface movement, air activity, official advisories, environmental context,
GPS disruption reporting, and strategic infrastructure.

Shipped platform capabilities:

- Cross-source global map with live and reference layers in one surface
- Convergence zones computed from multi-source overlap rather than single-source alerts
- Geometry-aware rendering for points, circles, routes, and polygons
- Intel tables for high-value notice, disruption, and advisory queues
- NOTAM intel rows and recent cards can jump the map to airport coordinates
  using bundled airport reference data even when the source only exposes an
  airport designator
- Advisory and incident tables for maritime, navigation, airspace, and safety
  context
- Two-slot intel briefing queue with persistent ordering, promote controls, and
  compact-screen handling
- Rule-based hypotheses with evidence event IDs and confidence tiers
- Space-environment context for geomagnetic and HF risk
- GPS interference attribution using environmental, notice, and constellation
  health context together
- Ocean-state mesh and wind overlay from sparse maritime sensor networks
- Detail panel with observation, ingest, expiry, and geometry context
- Source health reporting with explicit live, cache-backed, and failed states
  for slower reference collectors
- Layer toggles now mirror stale, cache-backed, and down source state
  directly, and map-feed caps disclose "showing X of Y" when the API limit is hit
- Optional deployment access control with short-lived browser sessions for
  protected installs
- Reference infrastructure overlays for energy, datacenter, and strategic
  nodes such as cable landings, converter stations, and industrial chokepoints
- Static maritime reference overlays for submarine cables, vessel-routing
  measures, EEZ boundaries, maintained shipping lanes, and exploration areas
- Derived maritime context in detail views: EEZ membership, maintained-route
  membership, nearest cable distance, routing-control context, and exploration
  area membership where reference data exists
- Runtime snapshots and key caches now persist through the application data
  path instead of resetting with image-local state
- Thermal anomaly alerts that pivot directly into nearby infrastructure context
- Radius-based proximity query with explicit distance ranking and nearby
  datacenter context for local investigative triage
- Vessel-in-zone correlation: FleetLeaks sanctioned vessels cross-referenced
  against TankerTrackers polygons at API serve time, with LNG/tanker alerts for
  Hormuz, Bab-el-Mandeb, and Suez zones
- Convergence popup contributor breakdown showing signal family weights, event
  counts, and contributing event IDs for each scored grid cell
- Progressive zoom disclosure: dense real-time layers (AIS, aircraft, VIIRS)
  suppressed at world zoom, rendered on drill-down without a refetch
- GPS disruption events annotated with orbital visibility context to separate
  jamming-like patterns from plausible environmental interference
- Deep-ocean pressure anomaly context for tsunami and underwater event triage
- Aircraft fuel-burn context when a tracked airframe can be matched reliably
- Onboarding, keyboard shortcuts, and clearer feedback states for refresh,
  collection, and briefing actions

What it does not do:

- It does not aggregate social media.
- It does not scrape news and relabel it as intelligence.
- It does not hide uncertainty behind a single composite score.

## Disclaimer

All data provided by this platform is offered "as is" and "as available",
without any warranties of any kind, whether express or implied.

No guarantees are made regarding the accuracy, reliability, completeness, or
timeliness of the data.

Users are solely responsible for independently verifying any information before
relying on it for operational, navigational, legal, or commercial purposes.

## Data Acknowledgements

- Aircraft state and flight-position context are powered in part by
  [The OpenSky Network](https://opensky-network.org).
- Airport reference coordinates used for NOTAM airport fallback and airport-centred
  map jumps are sourced from [`mwgg/Airports`](https://github.com/mwgg/Airports).
  The full Phantom Tide application bundle includes the airport reference JSON
  used for that lookup path at runtime; this public-docs repo does not duplicate
  the data file.
- Thanks to `mwgg/Airports` and alexander-san for their contribution and
  collaboration around the project and this release.

---

## Why It Is Different

Most maritime tools are good at one of these jobs:

- show vessel positions
- show incidents
- show weather
- show advisories

Phantom Tide is built for the boundary between them.

Examples:

- A vessel broadcasts position A while satellite detection suggests position B.
- A GPS interference advisory is live, but space-weather conditions suggest a
  natural ionospheric explanation may be plausible.
- Traffic disappears from a corridor while warnings and weather remain active.
- Aircraft hold near a maritime disruption area while the sea picture below
  changes.

The platform is strongest when multiple weak signals become one strong question.

---

## What Is Live Right Now

The public docs describe the live stack in capability terms rather than as a
provider-by-provider source inventory.

Current integrated coverage includes:

- Surface vessel tracking from `AIS (limited)`, plus slower vessel watchlist,
  sanctioned-fleet, and zone-crossing context
- Public aircraft movement context with tracked-airframe enrichment and alerting
- Multiple official maritime, navigation, airspace, and safety notice channels
- Thermal, low-light, ocean-state, deep-ocean, geophysical, and
  space-environment indicators
- GPS disruption context combining field reports, constellation health, and
  environmental conditions
- Strategic and jurisdictional reference overlays for routes, facilities,
  infrastructure, and selected industrial chokepoints
- Analyst-facing correlation tooling such as proximity ranking,
  vessel-in-zone detection, and cross-source risk surfaces

---

## What It Reveals Well

![North Atlantic — weather mesh and vessel density](docs/screenshots/atlantic.png)
*North Atlantic mid-zoom. Environmental context changes how every movement
pattern should be interpreted.*

Phantom Tide is particularly useful for:

- dark-vessel and AIS-contradiction workflows
- GPS interference triage
- airspace and maritime overlap analysis
- advisory-heavy regional monitoring
- identifying when multiple public signals start telling the same story

It is less useful if the task is only "show me this ship" or "show me the
latest headlines."

---

## Platform Views

### Risk Zones

![Risk zones — Persian Gulf and Red Sea](docs/screenshots/risk_zones.png)
*Risk zones are computed from cross-source convergence. A serious zone should
exist because independent signals overlap, not because a designer drew it.*

### Ocean State Layer

![Weather mesh — North Atlantic sensor network](docs/screenshots/weather_mesh.png)
*Wave and wind context from sparse sensor networks, rendered as a continuous
field for operational reading rather than a pile of isolated station markers.*

### Event Detail

![Event detail — HYDROLANT ice hazard broadcast warning](docs/screenshots/detail_panel.png)
*Detail view keeps the source, geometry, and time semantics visible. A map pin
without provenance is decoration.*

### Proximity Query

![Proximity query — English Channel 100nm radius](docs/screenshots/proximity_results.png)
*Right-click any position to rank nearby activity with explicit distance and
datacenter context across source types. Useful for drilling into a corridor,
port approach, or disruption cell.*

### Intel Tables

![Intel tables panel](docs/screenshots/intel_tables.png)
*Structured analyst tables keep high-value sources readable and jump the map to
the relevant area without forcing a layer hunt.*

---

## Current Feature Set

Analyst-facing features available now:

- layer toggles with per-layer counts
- layer toggles with stale/cache/down badges
- reduced-motion aware map interaction
- clickable intel rows with detail-panel preservation
- geometry-aware jump targets
- "showing X of Y" transparency for intel-table and capped map/API layer limits
- proximity-query tables with explicit distance-ranked event and datacenter rows
- plain-English space-weather status instead of provider jargon
- on-demand hypothesis evaluation endpoint

Known limitations:

- Dense point rendering depends on culling and restraint at world zoom
- Convergence scoring is live but several weight families are still in
  development, including AIS spoof/gap, dark-vessel, and aircraft-loiter signals

---

## Coming Next

Upcoming work already identified in the roadmap:

- richer orbital context for disruption-event attribution
- denser marine weather and ocean-state context
- additional coastal alert geometry in selected regions
- aviation weather and hazard context around key ports and airfields
- deeper underwater-event and anomalous-pressure correlation
- richer scored-cell drilldown so operators can inspect the exact evidence mix
- stronger vessel-watchlist and queueing workflows
- selected polar and Indian Ocean context layers where they improve contradiction reading

These are planned items, not implied capabilities.

---

## Access

Public documentation, release notes, and issue tracking are open at
[github.com/tg12/phantomtide](https://github.com/tg12/phantomtide).

The live instance is available at
[phantom.labs.jamessawyer.co.uk](https://phantom.labs.jamessawyer.co.uk).

### Starter Edition

Some public-facing Phantom Tide deployments use a lighter `starter` edition to
keep the live experience fast, focused, and easy to explore.

- Selected high-activity layers may appear in preview mode.
- The public surface stays centered on the core investigative workflow rather
  than the deepest live volume.
- Higher-access deployments may expose more depth where appropriate.

If you need more access than the public-facing starter edition currently
offers, [request access or an API key](https://github.com/tg12/phantomtide/issues/new?template=access_request.md).

If you already have an access key, use the `Access` button in the dashboard
header and paste the key into the access dialog for that browser session.

The aim is straightforward: keep the public-facing experience responsive while
presenting a cleaner, more approachable entry point into the platform.

## Incident Notes

- Public-safe outage write-ups live in [docs/oom-postmortem.md](docs/oom-postmortem.md) and [docs/geojson-cpu-outage.md](docs/geojson-cpu-outage.md).
- The 2026-04-01 deep dive is [How py-spy Became a Godsend When Phantom Tide's GeoJSON Path Ate the CPU](docs/geojson-cpu-outage.md).
- The matching technical appendix is in [docs/geojson-cpu-triage.md](docs/geojson-cpu-triage.md).

---

## Feedback

This repository is the public interface for feedback. The application code
itself is not published here.

| | |
|---|---|
| [Report a bug](https://github.com/tg12/phantomtide/issues/new?template=bug_report.md) | Something is broken or behaving unexpectedly |
| [Request a feature](https://github.com/tg12/phantomtide/issues/new?template=feature_request.md) | A concrete capability the platform should add |
| [Request access / API key](https://github.com/tg12/phantomtide/issues/new?template=access_request.md) | Ask for expanded access beyond the public starter edition |
| [General feedback](https://github.com/tg12/phantomtide/issues/new?template=feedback.md) | Workflow notes, questions, or review comments |
| [All open issues](https://github.com/tg12/phantomtide/issues) | Existing public feedback |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

*Phantom Tide - JS Labs*
