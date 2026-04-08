# Phantom Tide Operator Guide

Use this page if you need the working loop, not the product brief.

Live guide: https://phantom.labs.jamessawyer.co.uk/docs/guide/

## Start with the map

- World zoom is a triage surface, not a complete traffic plot.
- Read header state first: mode, last update, next refresh, and access status.
- Open Layers when a source matters; dense live layers are intentionally suppressed at low zoom.

## Read source state correctly

- `Live`: current ingest succeeded.
- `Degraded`: the source answered, but completeness or quality fell.
- `Stale`: old or cached data is still visible so the picture stays usable.
- `Tier-limited`: the feature exists, but the current session is capped intentionally.

Do not treat an empty map as proof of absence until you have checked zoom, time window, and source health.

## Tracked aircraft

- Use the alert banner or aircraft intel table to jump to the aircraft.
- Open detail before trusting the icon alone.
- Pull track history when the question is movement, not just presence.

## Convergence zones

- Convergence is a triage layer, not a verdict.
- Read score, evidence families, contributor weights, and recent change together.
- Drill in before assuming a low-density world view means nothing is happening.

## Proximity query and Area Intelligence Report

- Right-click the map to query a radius.
- Use Proximity Query for ranked nearby context.
- Use Area Intelligence Report for a deterministic plain-text sitrep tied to a visible circle.

## Adaptive mode

- `Teach / tutorial`: full prompts and explicit guidance.
- `Deep / analytical`: denser context and fewer reminders.
- `Fast / browsing`: shorthand copy and keyboard cues.

Only help density adapts automatically. Map controls, source colors, severity meaning, and click paths stay fixed for trust and muscle memory.

## Reversible actions

- `?` opens the in-app guide and shortcut sheet.
- `Escape` closes drawers, dialogs, and menus.
- `t` toggles relative and UTC time.
- `i` opens or closes intel briefings.
- `j` and `k` move through the live briefing rows.
- `Enter` opens the current row in Detail.
- `f` focuses the map on the current row or selected signal.

## Ask these three questions

1. Which signals overlap that should not overlap?
2. Which sources disagree about location, timing, or presence?
3. What is the freshest trustworthy path to a plain-language sitrep?
