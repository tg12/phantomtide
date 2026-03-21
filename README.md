# Phantom Tide

**Global Maritime Intelligence Platform**

> Most platforms show you what is there. This one shows you what is missing — and where.

---

The ocean broadcasts constantly. Vessel positions. Airspace closures. Sea state readings. Satellite detections. Official warnings. Phantom Tide ingests all of it simultaneously from nine independent streams and asks a single question: where does the physical record contradict the official one?

The signal is in the gap.

51,000+ live events. 30-second refresh. Global coverage.

---

![Phantom Tide — full dashboard overview](docs/screenshots/overview.png)
*Full dashboard. Nine independent data pipelines converging on a single live map. Risk zones computed from cross-source agreement — the more independent streams that converge on the same area, the higher the score.*

---

## The core insight

Most dashboards are mirrors. They reflect what vessels report, what authorities publish, what sensors transmit. Phantom Tide treats those broadcasts as claims — and checks them against independent physical evidence.

A vessel can lie about its position. An authority can issue a notice without explanation. A sensor can go silent. The interesting question is never "what is being reported" — it is "what does the physical record say, and does it match?"

When it does not match, Phantom Tide flags the contradiction, locates it precisely, and shows you everything else in the area.

**Absence is the signal. Presence is the baseline.**

---

## What it surfaces

A vessel transmitting position A while passive satellite detection places it at B.

GPS interference radiating outward from a fixed point across three consecutive days.

An exercise cancelled six days before its declared end date. No explanation on record.

Mine-hazard warnings appearing in shipping lanes that were clear last week.

A distress activation in a zone with no advisory and no follow-up traffic.

Aircraft in a holding pattern fifty miles from a known spoofing corridor.

A region where the risk score is climbing — not because one warning appeared, but because four independent streams are converging on the same coordinates simultaneously.

Phantom Tide does not tell you what these mean. It tells you they exist, where they are, when they were first detected, and what else is nearby.

---

## Platform

### Live intelligence map

![North Atlantic — weather mesh and vessel density](docs/screenshots/atlantic.png)
*North Atlantic. Continuous sea state field interpolated from sparse sensor networks — triangle opacity encodes data confidence. Dense coverage is opaque; sparse coverage fades. Vessel tracks visible as directional markers.*

---

### Risk zone overlay

![Risk zones — Persian Gulf and Red Sea](docs/screenshots/risk_zones.png)
*Persian Gulf and Red Sea. CRITICAL zones emerge where multiple independent warning streams converge on the same grid cell. At world scale only the highest-scoring zones are labelled — zoom in and the resolution increases.*

---

### Ocean state layer

![Weather mesh — North Atlantic sensor network](docs/screenshots/weather_mesh.png)
*Wave height and wind field across the North Atlantic. Airspace restriction geometry visible in teal — full polygon footprints, not centroid pins. The distinction matters: a centroid places an exclusion zone at its centre; the polygon shows you its actual boundary.*

---

### Event detail

![Event detail panel — AIS vessel](docs/screenshots/detail_panel.png)
*Selected feature detail. Time provenance bar shows when the phenomenon was observed versus when this system learned about it — a distinction that matters for delayed or cached sources. Expiry status for events with a declared end time.*

---

### Proximity query

![Proximity query — Persian Gulf 100nm radius](docs/screenshots/proximity_results.png)
*Right-click any point on the map and query everything within a chosen radius. Persian Gulf — 100nm query returns all active events ranked by source and distance. Everything outside the radius dims. The contradictions inside it surface.*

---

### Intel tables

![Intel tables panel](docs/screenshots/intel_tables.png)
*Structured tables for active advisories, critical notices, and recent warnings across all 19 tracked categories. Click any row to fly the map directly to that event. The tables are the dashboard's second axis — spatial on the map, categorical in the tables.*

---

## Warning categories

19 distinct categories. Each has its own colour, symbol, and classification logic. They are not cosmetic — they drive the risk scoring and the cross-source contradiction detection.

GPS Jamming &nbsp;·&nbsp; Mine Hazard &nbsp;·&nbsp; Piracy / Armed Robbery &nbsp;·&nbsp; Seismic / Tsunami &nbsp;·&nbsp; Volcanic Hazard &nbsp;·&nbsp; Rocket / Missile Range &nbsp;·&nbsp; SAR / Distress &nbsp;·&nbsp; Submarine Operations &nbsp;·&nbsp; Amphibious Operations &nbsp;·&nbsp; Military Exercise &nbsp;·&nbsp; Restricted Area &nbsp;·&nbsp; Naval Operations &nbsp;·&nbsp; Pollution / Spill &nbsp;·&nbsp; Wreck Hazard &nbsp;·&nbsp; Offshore Construction &nbsp;·&nbsp; Cable / Pipeline &nbsp;·&nbsp; Ice Hazard &nbsp;·&nbsp; Survey Operations &nbsp;·&nbsp; Navigational Warning

---

## What it does not do

It does not aggregate social media. It does not scrape news. It does not guess intent. It does not produce intelligence assessments.

It works with observable physical signals — positions, detections, official notices, sensor readings. When those signals agree, the map is quiet. When they disagree, the map tells you where and by how much.

Interpretation is yours.

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

See [CHANGELOG.md](CHANGELOG.md). Current release: **v1.8.2**

---

*Phantom Tide &mdash; JS Labs*
*&copy; 2026 James Sawyer*
