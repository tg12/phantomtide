# Phantom Tide

**Global Maritime Intelligence Platform**

> The ocean is not transparent. Most platforms pretend it is.

---

Phantom Tide is a live intelligence dashboard for analysts who need to know not just where things are — but where they aren't, and why.

It fuses multiple independent data streams in real time and surfaces the contradictions between them. Not what is being broadcast. What the broadcast is hiding.

The intelligence signal is the gap.

---

![Phantom Tide — full dashboard overview](docs/screenshots/overview.png)
*Full dashboard — 51,000+ live events across the global ocean surface. 30-second refresh.*

---

## What it reveals

A vessel broadcasting position A while a passive sensor shows it at position B.

An exercise cancelled six days before its scheduled end. No explanation on record.

Aircraft in a holding pattern fifty miles from a known spoofing corridor.

A distress activation in a zone with no advisory. No follow-up traffic.

Mine-hazard warnings appearing in shipping lanes that were clear last week.

GPS interference spreading from a fixed point across three consecutive days.

Phantom Tide does not tell you what these mean. It tells you they exist, where they are, and what else is nearby.

---

## Platform

### Live intelligence map

![North Atlantic — weather mesh and vessel density](docs/screenshots/atlantic.png)
*North Atlantic mid-zoom. Weather mesh shows continuous sea state interpolated from sensor networks. Triangle opacity encodes data confidence — dense coverage is opaque, sparse coverage fades. AIS vessel tracks visible as directional markers.*

---

### Risk zone overlay

![Risk zones — Persian Gulf and Red Sea](docs/screenshots/risk_zones.png)
*Persian Gulf and Red Sea. Cross-source risk scoring across a global grid. CRITICAL zones show where multiple independent warning streams converge. Labels emerge progressively as you zoom — at world scale only the highest-scored zones are visible.*

---

### Ocean state layer

![Weather mesh — North Atlantic sensor network](docs/screenshots/weather_mesh.png)
*North Atlantic wave height and wind field. Triangulated from sparse buoy sensor networks into a continuous field. NOTAM geometry overlays visible in teal — full polygon footprints, not centroid pins.*

---

### Event detail

![Event detail panel — AIS vessel](docs/screenshots/detail_panel.png)
*Selected feature panel. Vessel detail with observation timestamp, ingestion time, and coordinate copy. The time bar shows when the phenomenon was observed versus when this system learned about it — a distinction that matters for delayed or cached sources.*

---

### Proximity query

![Proximity query — Persian Gulf 100nm radius](docs/screenshots/proximity_results.png)
*Right-click any position to query all events within a chosen radius. Persian Gulf — 100nm query returns ranked results by source and distance. Everything outside the radius dims. The contradictions inside it surface.*

---

### Intel tables

![Intel tables panel](docs/screenshots/intel_tables.png)
*Bottom panel — structured tables for active advisories, critical notices, and recent warnings across all tracked categories. Click any row to fly the map directly to the event location.*

---

## What it does not do

It does not aggregate public social media. It does not scrape news. It does not guess intent.

It works with observable signals — positions, detections, official notices, sensor readings. When the physical record and the official record disagree, Phantom Tide shows you the disagreement.

Interpretation is yours.

---

## Warning categories

19 distinct categories, each with its own visual treatment:

GPS Jamming &nbsp;·&nbsp; Mine Hazard &nbsp;·&nbsp; Piracy / Armed Robbery &nbsp;·&nbsp; Seismic / Tsunami &nbsp;·&nbsp; Volcanic Hazard &nbsp;·&nbsp; Rocket / Missile Range &nbsp;·&nbsp; SAR / Distress &nbsp;·&nbsp; Submarine Operations &nbsp;·&nbsp; Amphibious Operations &nbsp;·&nbsp; Military Exercise &nbsp;·&nbsp; Restricted Area &nbsp;·&nbsp; Naval Operations &nbsp;·&nbsp; Pollution / Spill &nbsp;·&nbsp; Wreck Hazard &nbsp;·&nbsp; Offshore Construction &nbsp;·&nbsp; Cable / Pipeline &nbsp;·&nbsp; Ice Hazard &nbsp;·&nbsp; Survey Operations &nbsp;·&nbsp; Navigational Warning

---

## Access

Phantom Tide is not publicly available.

If you believe you have a use case, open an access request issue or contact directly.

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

See [CHANGELOG.md](CHANGELOG.md). Current release: **v1.8.1**

---

*Phantom Tide &mdash; JS Labs*
*&copy; 2026 James Sawyer*
