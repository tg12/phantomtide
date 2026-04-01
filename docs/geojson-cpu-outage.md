# How py-spy Became a Godsend When Phantom Tide's GeoJSON Path Ate the CPU

There is a kind of outage that flatters the wrong instincts.

The surface symptoms point toward infrastructure. Requests hang. Health checks stall. CPU is hot. The public site looks sick. The easy story writes itself: maybe the proxy is misbehaving, maybe the host is too small, maybe the quickest fix is to add workers and move on.

That story is attractive because it is broad enough to sound plausible and vague enough to avoid proving anything.

On 2026-04-01, Phantom Tide hit exactly that kind of outage.

The public dashboard stalled. `api/health` stalled. Internal health checks to the application container stalled too. From far enough away, it looked like generic backend distress.

From close enough, it turned out to be something much more specific: one request path had quietly become too expensive for how often it was being called, and `py-spy` was the tool that turned that suspicion into evidence.

This is the technical story of what we first thought, what we tried, what those attempts ruled out, what finally exposed the real fault, and why the final fix was less about cleverness than discipline.

## The first effect was public failure. The first cause we ruled out was the edge.

The opening symptom was external. The site was stalling. That naturally pushes attention toward the edge proxy, TLS termination, routing rules, and the usual network-adjacent suspects.

That line of thought collapsed quickly.

Direct internal probes to the backend container were timing out too. Once the application cannot answer inside its own network boundary, the problem is no longer primarily about public ingress. Cause and effect become much narrower:

- if public requests fail and internal requests succeed, the edge is a plausible suspect
- if public requests fail and internal requests fail too, the backend itself is the actual fault domain until proven otherwise

That one distinction saved a lot of wasted effort.

It did not solve the outage. It did something more important first. It stopped the investigation from wandering off into elegant but irrelevant theories.

## The next thing we knew was that the app was hot. The missing piece was hot doing what.

At this point the system had all the signals that often lead teams astray.

CPU was high. The application was slow. There was enough complexity in the stack to blame almost anything with a straight face: reverse proxying, worker churn, startup hydration, background roles, caches, database pressure, or just “too much load.”

That is the trap.

Resource graphs tell you that something is expensive. They do not tell you what code is spending the money.

This is exactly where `py-spy` stopped being a nice-to-have and became the most useful tool in the room.

## What we tried before the decisive answer

The useful early work in this incident was mostly elimination.

First, the edge path was checked and effectively ruled out because the backend was unhealthy even from inside the trusted network.

Second, runtime-role separation was already in place, which helped isolate one class of failure. The app-role process was not supposed to be doing scheduler ownership work. That reduced one plausible explanation, but it did not explain why the app worker was still running hot.

Third, health checks and logs were compared between the API-facing service and the worker-facing service. That mattered because it established that the image itself was not generically broken. The problem was not “the container cannot serve requests.” The problem was that one runtime path under one traffic pattern was burning through CPU in a way that starved unrelated endpoints.

All of that was useful.

None of it yet identified the exact mechanism.

That is the moment where many incidents go soft. Everyone has enough information to sound informed, but not enough to be precise.

## py-spy turned a vague performance incident into a concrete stack trace

The turning point was sampling the live Python worker instead of continuing to infer behavior from side effects.

This is why `py-spy` felt like a godsend in this incident.

It bypassed the storytelling layer.

Instead of asking what the application might be doing, it showed what the application was actually doing while it was hurting.

The hot worker consistently pointed into the same chain:

- the bulk GeoJSON endpoint
- maritime-context enrichment
- maritime reference-layer loading
- gzip and JSON parsing
- spatial index construction

That immediately changed the shape of the problem.

The failure was not an undifferentiated “API overloaded” condition. It was a specific request path doing specific CPU-heavy work while the rest of the application waited behind it.

Cause and effect snapped into place:

- the dashboard polled bulk GeoJSON repeatedly
- bulk GeoJSON paid for maritime-context enrichment by default
- maritime-context enrichment could trigger expensive static-layer work
- that CPU cost occupied the worker long enough to make even lightweight endpoints feel dead

Once that chain was visible, the outage stopped being mysterious.

## What failed conceptually was not just one function. It was permission.

This is the deeper lesson.

The problem was not merely that a route happened to be slow. The problem was that the busiest path in the system had been granted permission to perform expensive investigative work by default.

That is an architectural mistake before it is a performance mistake.

The default map feed is the path most likely to be hit repeatedly. That means it should be biased toward predictable, bounded work. Instead, it had accumulated three costly behaviors at once:

- it assembled large bulk responses
- it enriched each feature with maritime context by default
- it could rebuild or reload maritime reference structures during live request handling

That is how a route that looks routine in a routing table becomes the real outage engine under load.

This is also why the obvious fix of “add more workers” was the wrong instinct.

If the cost per request is fundamentally wrong for the most frequently polled endpoint, more workers do not correct the design. They just change how broadly the design can fail.

## The async route was not the root cause, but it widened the blast radius

One subtle part of the failure was the route shape itself.

The GeoJSON handler was defined as an async route, but the expensive work inside it was not really async work. It was synchronous CPU work: response assembly, compressed payload loading, JSON parsing, and spatial index building.

That distinction matters.

An async route is useful when it mostly coordinates non-blocking operations. It is a poor place to hide long synchronous CPU stretches, because that turns the event loop into a queue behind work it cannot preempt.

So the honest technical answer is not “async was bad.”

The honest answer is more specific:

- async was not the root bug
- synchronous CPU work inside that async path made the failure hurt more broadly

That nuance matters because it determines the fix. The goal is not to be ideological about sync versus async. The goal is to stop the wrong kind of work from monopolizing the wrong execution path.

## What finally fixed it

The resolution was not one dramatic change. It was a small set of changes that all moved in the same direction: remove optional heavy work from the hottest path and make static reference costs behave like static reference costs.

The most important changes were these.

First, maritime enrichment on bulk GeoJSON became opt-in instead of default. That reversed the most expensive mistake directly. Analyst-grade context remained available, but it stopped being charged to every ordinary polling request.

Second, maritime reference caching switched from short TTL expiry to file-signature invalidation. Static layers now rebuild when their underlying files actually change, not because a timer happened to roll over while requests were live.

Third, the heavy route stopped monopolizing the event-loop thread during synchronous CPU work.

Each of those changes is simple to describe on its own. Together they corrected the cause-and-effect chain that produced the outage.

The endpoint became cheaper by default.

Static data became genuinely static from the cache's point of view.

And lightweight endpoints were no longer forced to wait behind the wrong kind of work.

## What did not work as an answer

This is worth stating directly because these are exactly the kinds of answers that often survive inside postmortems longer than they deserve.

These were not the real answers:

- blaming the proxy because the site was public-facing
- assuming more workers would solve a bad per-request cost structure
- treating high CPU as sufficient explanation by itself
- treating runtime-role separation as proof that the hot path had been fixed

Those ideas were adjacent to the incident. They were not the incident.

The real value of `py-spy` here was that it removed the need to argue about adjacency.

## Why this matters beyond this one release

This bug says something broader about the system.

Phantom Tide is not hard because it has a map. It is hard because it has to decide, constantly and correctly, which intelligence features belong on the critical path and which ones must stay behind an explicit request boundary.

That is the actual engineering problem in systems like this.

If expensive analysis leaks into the operational default path, the system will feel impressive right up until the day it becomes brittle. Then every nice feature turns into evidence against the architecture.

This incident forced a cleaner rule into the platform:

the most frequently hit path should not pay for optional investigative depth unless that cost has been made explicit and proven safe.

That is a much more useful lesson than “CPU was high.”

## Why publish this at all

The code fix mattered.

The write-up mattered too.

Incidents like this are where a system reveals what it actually is. If the lesson is not written down while the chain of evidence is still clear, the memory decays into folklore: the API was slow one day, some caching got changed, probably there was load.

That version is useless.

The public-safe version is worth preserving because it captures the real sequence:

- what failed first
- what that failure seemed to imply
- what was tried and ruled out
- what `py-spy` finally proved
- what changed in response

The earlier OOM write-up showed why Phantom Tide needed memory discipline. This incident showed why it needed request-path discipline too.

And if there is one practical recommendation that survives all the narrative around it, it is this:

when Python in production is hot and your explanation still sounds atmospheric, stop telling stories about the graph and sample the process.

That is usually where the real cause is hiding.