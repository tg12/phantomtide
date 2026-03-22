# Changelog

All notable changes to Phantom Tide are recorded here.

Dates are UTC. Versions follow semantic versioning.

---

## v1.9.1 — 2026-03-22

**Hotfixes from deployment hardening regression**

Three bugs introduced in v1.9.0 deployment hardening, fixed immediately.

- **Collectors silently broken** — `USER phantom` (non-root container user) could not write to Docker-managed volumes that were created under root in prior runs. NDBC, NGA_MIS, DailyMem, and NOTAM collectors all write file caches to `/app/data/`; VIIRS and AIS appeared unaffected because VIIRS loaded from a pre-existing volume and AIS is pure in-memory. Non-root user reverted. The correct fix for a hosted deployment is an entrypoint script that fixes volume ownership before dropping privileges — noted in roadmap.
- **App port removed** — `docker-compose.yml` changed app from `ports: 8000:8000` to `expose` only, making it unreachable without going through Caddy. Restored `8000:8000` for local dev. Caddy remains available at `:80` for proxy-layer testing.
- **Intel table row click** — clicking any row in the NOTAM, DailyMem, or SMAPS intel tables was closing the table and not flying the map to the item. Root cause: `closeTablesPanel()` was called before `focusMapOnLocation()`, and the `map.invalidateSize()` triggered inside `closeTablesPanel()` via `requestAnimationFrame` fired after the flyTo animation started, cancelling it mid-flight. Fixed by removing `closeTablesPanel()` from all three table click handlers. Table now stays open; map pans correctly.

---

## v1.9.0 — 2026-03-22

**Public-facing redesign, deployment hardening, documentation consolidation**

### Public site

- CSS design system rewritten (`frontend/css/site.css`). Removed frosted glass, warm paper gradient, pill buttons, and shadows — replaced with a flat dark cool palette (`#0c1925` base), accent-bordered cards, 4px-radius square buttons, and a monospace footer. Light theme roadmap added as commented variable set for future implementation.
- About page: Open Graph, Twitter Card, and JSON-LD structured data (`WebPage` + `SoftwareApplication` schema) added for SEO and social sharing. Above-the-fold hero CTA pair added (primary + outline). Licensing section expanded with commercial restriction and safety limitation language.
- Legal notice page completely rewritten. Now covers: acceptance, IP ownership, permitted and restricted use, safety-critical system exclusion, no professional advice, third-party data, accuracy limitations, no-warranty clause (ALL CAPS), limitation of liability (ALL CAPS, £100 cap), indemnification, export/sanctions compliance, governing law, severability, entire agreement. Breadcrumb JSON-LD added.

### Deployment hardening

- `.dockerignore` added. Excludes `secrets/`, `.env*`, `.git/`, `__pycache__`, tests, and documentation from the build context — live credentials can no longer be baked into an image.
- `Dockerfile`: removed `pip install --upgrade` (versions now pinned to `requirements.txt` at build time); added `phantom` non-root system user; container now runs as `USER phantom`.
- `docker-compose.yml`: all internal service ports (`5432`, `8123`, `9000`, `6379`) changed from `ports:` to `expose:` — not reachable from the host. Hardcoded passwords replaced with `${VAR}` env var references; `POSTGRES_PASSWORD`, `CLICKHOUSE_PASSWORD`, and `MINIO_SECRET_KEY` have no defaults and require `.env`. `minio:latest` pinned to a specific release tag. Named `internal` bridge network added isolating all services. `CADDY_DOMAIN` threaded through to Caddy service.
- `infra/caddy/Caddyfile`: `{$CADDY_DOMAIN::80}` pattern — HTTP-only locally, automatic HTTPS in production by setting `CADDY_DOMAIN`. Security headers added: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`, scoped `Content-Security-Policy` (CartoDB/OSM tiles allowlisted). `Server` and `X-Powered-By` headers removed. gzip + zstd compression. Upstream health check via `/api/health`.
- `run.sh`: `ensure_env()` added — creates `.env` from `.env.example` on first run and auto-generates 48-char hex random passwords for `POSTGRES_PASSWORD`, `CLICKHOUSE_PASSWORD`, and `MINIO_SECRET_KEY` if blank; idempotent on subsequent runs. Port check updated to 80/443 only (DB ports no longer host-bound). Launch banner updated to reflect Caddy entrypoint.
- `.env.example`: `POSTGRES_HOST` default corrected to `postgis` (matches Compose service name); `NOTAM_REST_URL` entry added.

### Documentation

- Deleted stale files: `CHANGE_LOG_AGENT_NOTES.txt`, `UI_UX_ISSUES_AND_REQUIREMENTS.txt`, `UI_UX_WIREFRAME_AND_RECOMMENDATIONS.txt`, `REDDIT_BRIEF.txt`, `NAV_WARNINGS_SOURCE.txt`.
- `PHANTOM_TIDE_ROADMAP.txt` rewritten. Stripped session-by-session build log (preserved in git). Added Design Principles section (subtraction first, priority-driven, progressive disclosure, analyst-first workflow, visible memory, time consistency) and four open strategic questions for the next UX sprint.
- `LAUNCH_BRIEF.txt` added: internal positioning document covering competitive differentiation vs. vessel trackers, geopolitical aggregators, and professional platforms. Includes honest review campaign spec.
- `REDDIT_POST_DRAFT.txt` added: post draft for r/OSINT, r/geospatial, r/netsec, r/maritime with per-subreddit angle notes and honest review / beer offer.
- `README.md` and `DATA_SOURCES.txt` updated to reflect current collector state.

---

## v1.8.2 — 2026-03-21

**Collector fix: NOTAM and DailyMem restored**

Both NOTAM and DailyMem broadcast warning collectors were failing silently on every cycle due to a Python 3.14 / pydantic v1 incompatibility in the shared text enrichment layer. The enrichment module was designed with a graceful fallback, but the exception guard was too narrow — it caught `ImportError` only, not the `ConfigError` that pydantic v1 raises when it cannot infer a type under Python 3.14. Both collectors now operate cleanly and produce full output on every cycle.

- NOTAM: restored, collecting via SWIM JMS
- DailyMem: restored, all five NAVAREA/HYDROPAC files parsing
- Text enrichment fallback now activates correctly when the primary NLP pipeline is unavailable

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
