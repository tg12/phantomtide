# Phantom Tide GeoJSON CPU Triage Snapshot

Date: 2026-04-01

## Short version

- Cause: CPU saturation in the backend request path, not at the public edge.
- Immediate effect: the dashboard and even lightweight health endpoints stalled behind heavy GeoJSON work.
- Decisive evidence: `py-spy` samples tied the hot worker to GeoJSON assembly, maritime enrichment, and maritime reference-layer index work.
- Release status: fixed in `v1.33.0`.

## Cause and effect chain

1. The dashboard repeatedly hit the bulk GeoJSON endpoint.
2. That endpoint paid for maritime-context enrichment by default.
3. Maritime-context work could trigger static-layer loading, gzip and JSON parsing, and spatial index construction during live request handling.
4. The worker stayed busy long enough that unrelated lightweight routes also appeared unhealthy.

## What was tried and ruled out

- Edge proxy failure: ruled out because direct internal backend checks stalled too.
- Generic image corruption: ruled out because the same application image could still answer in the worker runtime path.
- Pure concurrency shortage: not sufficient as an explanation, because the hot path itself was doing the wrong work for a frequently polled endpoint.

## What finally exposed the real fault

Live `py-spy` sampling showed the hot worker spending CPU in:

- bulk GeoJSON response generation
- maritime-context enrichment
- gzipped layer loading and JSON parsing
- spatial index construction

That turned the incident from a vague performance problem into a concrete request-path failure.

## What changed in the shipped fix

- Bulk GeoJSON no longer performs maritime enrichment unless it is explicitly requested.
- Maritime cache invalidation now follows source-file versions instead of a short TTL.
- The heavy GeoJSON path no longer monopolizes the event-loop thread during synchronous CPU work.
- Local operator images include `py-spy`, and local Docker compose grants the ptrace permissions needed for future live sampling.

## What is still not proven

- Replay/backtest coverage is still not the gate for future score changes.
- VIIRS retention is still not bounded by an explicit cleanup job.
- Redis restart recovery still needs an operator-proof rebuild path.

## Counterintuitive truth

The winning move was not to add more workers.

The winning move was to stop making the busiest endpoint pay for optional investigative depth on every poll.

## Next release focus

- first replay/backtest harness
- VIIRS retention and pruning
- Redis recovery discipline
- selective source triage with measured contradiction value