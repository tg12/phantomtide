# Phantom Tide

**Global Maritime Intelligence Platform**

> The ocean is not transparent. Most platforms pretend it is.

---

Phantom Tide is a live cross-domain intelligence dashboard built on a single architectural conviction: that the most significant events at sea are not what is being broadcast — they are the contradictions between what is broadcast and what independent physical evidence shows.

It answers three questions simultaneously, without clicking:

1. **Where** is the highest risk right now?
2. **What** is driving that risk?
3. **How certain is the signal** — and how much is noise?

Noise is not hidden. It is displayed explicitly. A risk score driven by a single source looks different from a score driven by multi-source corroboration. That distinction is the product.

---

![Phantom Tide — full dashboard overview](docs/screenshots/overview.png)
*Full dashboard — 51,000+ live events across the global ocean surface. Risk zones emerge from cross-source convergence, not from any single data stream. 30-second refresh.*

---

## What makes it different

Most maritime tools are single-domain. They show vessel positions, or piracy incidents, or weather. Some show two of these. They are useful for what they do.

Phantom Tide fuses nine independent streams across five domains simultaneously:

**Vessel positions** — broadcast positions from vessels at sea, quality-scored and tracked over time.

**Satellite detection** — passive sensor data from orbital systems that does not depend on a vessel's willingness to broadcast. A vessel can silence its transponder. It cannot silence a satellite.

**Ocean sensor networks** — live physical environment readings from instrumented buoys: wave height, wind speed, sea state, temperature. Environmental context that changes the interpretation of everything else.

**Maritime broadcast warnings** — the raw official safety publications transmitted to vessels at sea across global nav areas. Not a sanitised API summary. The actual source text, parsed in full, with full polygon geometry. This is the layer that captures GPS jamming corridors, mine hazard areas, live-fire exercise zones, submarine operations, and 15 other categories — updated daily from the authoritative source.

**Airspace** — active airspace notices, rendered as full polygon footprints rather than centroid pins. Cross-referenced with maritime activity below them.

**Aircraft positions** — live air traffic, connecting the air and sea pictures in a single view.

**Piracy and incident records** — historical and current incident data across global maritime corridors.

**Drilling platform positions** — offshore operational unit locations, clustered by field proximity, tracked for drift.

**Cross-domain risk scoring** — a computed grid that accumulates signal weight from all active streams simultaneously. When multiple independent sources converge on the same coordinates, the risk score rises. When they diverge, the contradiction is flagged.

The core insight this is built on: **absence is the signal**. AIS present is normal. AIS absent in a cell where satellite detection is active is the interesting event. A nav warning active in a corridor where vessel traffic has dropped is worth looking at. The platform is designed to surface these gaps, not hide them.

---

![North Atlantic — weather mesh and vessel density](docs/screenshots/atlantic.png)
*North Atlantic mid-zoom. The weather mesh is a continuous sea state field interpolated from sparse buoy networks — triangle opacity encodes sensor confidence. Dense coverage is opaque; sparse coverage fades. Vessel tracks visible as directional markers.*

---

## What it reveals

A vessel transmitting position A while passive satellite detection places it at B.

GPS interference radiating outward from a fixed point across three consecutive days.

An exercise cancelled six days before its declared end date. No explanation on record.

Mine-hazard warnings in shipping lanes that were clear last week.

A distress activation in a zone with no advisory and no follow-up traffic.

Aircraft in a holding pattern fifty miles from an active spoofing corridor.

A region where the composite risk score is climbing — not because one warning appeared, but because four independent streams are converging on the same grid cell simultaneously.

Phantom Tide does not tell you what these mean. It tells you they exist, where they are, when they first appeared, and what else is nearby.

---

## Platform

### Risk zone overlay

![Risk zones — Persian Gulf and Red Sea](docs/screenshots/risk_zones.png)
*Persian Gulf and Red Sea. Risk zones are computed from cross-source agreement — not manually drawn. CRITICAL zones emerge where multiple independent warning streams converge on the same area. At world scale only the highest-scoring zones are labelled; zoom in and resolution increases.*

---

### Ocean state layer

![Weather mesh — North Atlantic sensor network](docs/screenshots/weather_mesh.png)
*Wave height and wind field across the North Atlantic. Airspace restriction geometry in teal — full polygon footprints, not centroid pins. A centroid places an exclusion zone at its centre. The polygon shows its actual boundary.*

---

### Event detail

![Event detail panel — AIS vessel](docs/screenshots/detail_panel.png)
*Selected feature detail. The time bar distinguishes when a phenomenon was observed from when this system learned about it — a distinction that matters for delayed or cached sources. Events with a declared end time show expiry status.*

---

### Proximity query

![Proximity query — Persian Gulf 100nm radius](docs/screenshots/proximity_results.png)
*Right-click any position. Query all active events within a chosen radius. Everything outside the radius dims. The contradictions inside it surface.*

---

### Intel tables

![Intel tables panel](docs/screenshots/intel_tables.png)
*Structured tables for active advisories, critical notices, and broadcast warnings across all 19 tracked categories. Click any row to fly the map directly to that event.*

---

## Warning categories

19 categories. Each has independent classification logic, its own visual treatment, and feeds directly into the cross-source risk layer.

GPS Jamming &nbsp;·&nbsp; Mine Hazard &nbsp;·&nbsp; Piracy / Armed Robbery &nbsp;·&nbsp; Seismic / Tsunami &nbsp;·&nbsp; Volcanic Hazard &nbsp;·&nbsp; Rocket / Missile Range &nbsp;·&nbsp; SAR / Distress &nbsp;·&nbsp; Submarine Operations &nbsp;·&nbsp; Amphibious Operations &nbsp;·&nbsp; Military Exercise &nbsp;·&nbsp; Restricted Area &nbsp;·&nbsp; Naval Operations &nbsp;·&nbsp; Pollution / Spill &nbsp;·&nbsp; Wreck Hazard &nbsp;·&nbsp; Offshore Construction &nbsp;·&nbsp; Cable / Pipeline &nbsp;·&nbsp; Ice Hazard &nbsp;·&nbsp; Survey Operations &nbsp;·&nbsp; Navigational Warning

---

## What it does not do

It does not aggregate social media. It does not scrape news. It does not guess intent.

It works with observable physical signals — positions, detections, official notices, sensor readings. When those signals agree, the map is quiet. When they disagree, Phantom Tide shows you the disagreement.

This is a research platform, not a certified intelligence product. Risk scores are heuristic aggregations of public open-data signals. They are not intelligence assessments and carry no official weight. Interpretation is yours.

---

## Access

Phantom Tide is not publicly available.

If you believe you have a use case, open an access request issue or contact directly. Requests without a stated context will not receive a response.

---

## Feedback

This repository is the public interface for platform feedback. Source code is not here.

| | |
|---|---|
| [Report a bug](https://github.com/tg12/phantomtide/issues/new?template=bug_report.md) | Something is broken or behaving unexpectedly |
| [Request a feature](https://github.com/tg12/phantomtide/issues/new?template=feature_request.md) | An idea for something the platform should do |
| [General feedback](https://github.com/tg12/phantomtide/issues/new?template=feedback.md) | Observations, questions, workflow notes |
| [All open issues](https://github.com/tg12/phantomtide/issues) | See what is already tracked |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Current release: **v1.8.2**

---

*Phantom Tide &mdash; JS Labs*
*&copy; 2026 James Sawyer*
