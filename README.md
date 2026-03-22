# Phantom Tide

**Global Maritime Intelligence Platform**

> Every other platform shows you what vessels report. This one shows you what vessels are hiding.

---

The ocean broadcasts constantly. Vessel positions. Official warnings. Sea state readings. Satellite detections. Airspace notices. Nine independent streams, running simultaneously, cross-checked against each other in real time.

Most platforms pick one stream and call it a map.

Phantom Tide asks a different question: **where does the physical record contradict the official one?**

51,000+ live events. Nine independent pipelines. 30-second refresh. Global coverage.

---

![Phantom Tide — full dashboard overview](docs/screenshots/overview.png)
*Full dashboard. Nine independent data pipelines converging on a single live map. Risk zones emerge where multiple independent warning streams converge — the more independent sources agree, the higher the score, the more certain the signal.*

---

## The landscape

Every maritime platform in public use is an AIS mirror.

[Marine Cadastre](https://hub.marinecadastre.gov/pages/vesseltraffic) is a NOAA/BOEM planning tool, built in 2007 for offshore energy regulators. It serves archived historical vessel density charts. The most recent data available as of this writing is a batch labelled "October to December 2025." It is not a live intelligence tool. It was never designed to be.

[MarineTraffic](https://www.marinetraffic.com). [VesselFinder](https://www.vesselfinder.com). [Vesseltracker](https://www.vesseltracker.com). These are directories with a map layer. They show you what ships claim, where they claim to be. They do not ask whether the claim is true. When a vessel goes dark, the dot disappears. That is considered normal. Nothing flags it.

[Global Fishing Watch](https://globalfishingwatch.org) is a single-domain tool for fishing vessel monitoring. One data type. One sector. Narrow by design. It uses AIS. AIS is self-reported.

[Beholder](https://beholder.me) does not load.

**The common failure mode:** every one of these platforms treats a vessel broadcast as ground truth. The moment a vessel switches off its transponder — or spoofs its position, or drifts into a warned corridor — the platform has nothing to say. It shows the last known location and waits.

Phantom Tide does not wait. It has other sources running.

---

## What the other sources see

A vessel can silence its transponder. It cannot silence a satellite.

It cannot remove itself from the record of a maritime broadcast warning it entered. It cannot undo a GPS interference reading from a sensor network three hundred miles away. It cannot erase the track that ocean buoy telemetry has been recording while its AIS was off.

This is the operational difference. Not data volume. Not refresh rate. **Independent corroboration across streams that cannot be simultaneously manipulated.**

When position A (broadcast) diverges from position B (satellite), Phantom Tide flags the divergence. When a vessel disappears inside an active warning zone, it is not treated as a normal gap. When GPS interference spreads outward from a fixed point over three consecutive days, the system records the geometry of that spread.

No AIS mirror catches any of this. The vessel is simply gone.

---

## What it surfaces

A vessel transmitting position A while passive satellite detection places it at B.

GPS interference radiating outward from a fixed point across three consecutive days.

An exercise cancelled six days before its declared end date. No explanation on record.

Mine-hazard warnings appearing in shipping lanes that were clear last week.

A distress activation in a zone with no advisory and no follow-up traffic.

Aircraft in a holding pattern fifty miles from an active spoofing corridor.

A region where four independent streams are converging on the same coordinates simultaneously — and the risk score is climbing because of it.

Phantom Tide does not tell you what these mean. It tells you they exist, precisely where they are, when they were first detected, and what else is in the vicinity.

---

## Platform

### Live intelligence map

![North Atlantic — weather mesh and vessel density](docs/screenshots/atlantic.png)
*North Atlantic. Continuous sea state field derived from sparse sensor networks — triangle opacity encodes data confidence. Dense sensor coverage is opaque; sparse coverage fades. No AIS mirror shows this layer because no AIS mirror has it.*

---

### Risk zone overlay

![Risk zones — Persian Gulf and Red Sea](docs/screenshots/risk_zones.png)
*Persian Gulf and Red Sea. Risk zones are not drawn by hand. They are computed — derived from cross-source agreement across independent warning streams. CRITICAL zones emerge where multiple streams converge on the same grid cell. The score is not one source's opinion. It is the agreement of several independent ones.*

---

### Ocean state layer

![Weather mesh — North Atlantic sensor network](docs/screenshots/weather_mesh.png)
*Wave height and wind field interpolated across the North Atlantic from buoy sensor networks. Airspace restriction geometry shown in teal — full polygon footprints, not centroid pins. A centroid places an exclusion zone at its centre. The polygon shows its actual boundary.*

---

### Event detail

![Event detail panel — AIS vessel](docs/screenshots/detail_panel.png)
*Selected feature detail. The time bar shows when the phenomenon was observed versus when this system learned about it — a distinction that exposes delayed sources and cached feeds. Every event carries an observation timestamp, an ingestion timestamp, and an expiry field where applicable.*

---

### Proximity query

![Proximity query — Persian Gulf 100nm radius](docs/screenshots/proximity_results.png)
*Right-click any position. Query everything within a chosen radius. Persian Gulf — 100nm query returns all active events across all active streams, ranked by source and distance. Everything outside the radius dims. The contradictions inside it surface.*

---

### Intel tables

![Intel tables panel](docs/screenshots/intel_tables.png)
*Structured tables for active advisories, critical notices, and broadcast warnings. 19 tracked categories. Click any row to fly the map to that event. The tables surface what the map's spatial view flattens — categorical breadth, not just geographic density.*

---

## Warning categories

19 categories. Each has independent classification logic, its own colour encoding, and feeds directly into the risk scoring layer. They are not labels. They are inputs to the contradiction engine.

GPS Jamming &nbsp;·&nbsp; Mine Hazard &nbsp;·&nbsp; Piracy / Armed Robbery &nbsp;·&nbsp; Seismic / Tsunami &nbsp;·&nbsp; Volcanic Hazard &nbsp;·&nbsp; Rocket / Missile Range &nbsp;·&nbsp; SAR / Distress &nbsp;·&nbsp; Submarine Operations &nbsp;·&nbsp; Amphibious Operations &nbsp;·&nbsp; Military Exercise &nbsp;·&nbsp; Restricted Area &nbsp;·&nbsp; Naval Operations &nbsp;·&nbsp; Pollution / Spill &nbsp;·&nbsp; Wreck Hazard &nbsp;·&nbsp; Offshore Construction &nbsp;·&nbsp; Cable / Pipeline &nbsp;·&nbsp; Ice Hazard &nbsp;·&nbsp; Survey Operations &nbsp;·&nbsp; Navigational Warning

---

## What it does not do

It does not aggregate social media. It does not scrape news. It does not guess intent. It does not produce intelligence assessments or recommendations.

It works with observable physical signals — positions, detections, official notices, sensor readings. When those signals agree, the map is quiet. When they disagree, the map tells you exactly where and by how much.

**Interpretation is yours.**

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
