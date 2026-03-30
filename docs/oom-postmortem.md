# How I Dragged Phantom Tide Out of an OOM Kill Loop

There is a certain kind of technical failure that tells you more about a platform than any polished launch thread ever will.

Not when the UI looks clean. Not when the homepage loads fast. Not when the architecture diagram is neatly colour-coded and everyone is pretending the system is more deliberate than it really is. The real test is what happens when production turns hostile, memory gets tight, startup paths collide, caches swell, schedulers stampede, and the kernel starts killing your process like it has lost patience with your design.

That was the point where Phantom Tide became real.

From the outside, the symptom was boring: 502s across the site. From the inside, it was a systems failure spread across FastAPI, uvicorn, Redis, ClickHouse, APScheduler, Docker memory limits, and a startup sequence that had quietly become a deterministic self-attack.

What follows is the technical story of how I fixed it. But it is also the real story of what Phantom Tide actually is.

Because the uncomfortable truth is this: I did not build a map.

The map is just the visible surface. The real work was underneath it: source ingestion, event normalisation, scheduler behaviour, memory control, failure isolation, storage trade-offs, and the ugly operational logic required to make hostile upstream data behave like one coherent system. If you only look at Phantom Tide as a frontend product, you miss the engineering entirely. The map is just the proof that the machinery resolves into something legible. The machinery is the point.

## I thought I was fixing a crash loop. I was really exposing the architecture.

At first glance this looked like an ordinary outage. Phantom Tide started returning 502 Bad Gateway responses and the application container was restart-looping. That is the sort of thing a lot of people write off as “server trouble” until they burn hours chasing reverse proxies and restart counters.

I ignored the polite lies and went straight to the kernel.

`dmesg` made it clear almost immediately that this was not a routing issue or a generic application fault. The Python process was being killed by the OOM killer. The key signal was `anon-rss`, not total VM size, not Docker restart metadata, not container health status. Actual resident anonymous memory was blowing through the limit and the kernel was enforcing it.

That matters because once the kernel is killing your process, the question stops being “why is the site down” and becomes “which part of my system thinks it deserves this much memory, and why did I let it.”

That is the difference between debugging the symptom and debugging the system.

## The first problem: I was treating a stateful process like a stateless web app

The initial deployment was running uvicorn with four workers.

That is normal if your application is basically stateless request handling and you want cheap concurrency. It is a bad idea when your process contains mutable in-memory state, a scheduler, startup hydration logic, live buffers, and background collectors that assume singleton behaviour.

In that setup, four workers do not mean one application serving four times more efficiently. It means four copies of the same process state, four schedulers, four startup passes, four independent memory footprints, and four ways to multiply every mistake hidden in your boot logic.

That is not resilience. That is replication of instability.

So the first emergency change was brutally simple:

```sh
uvicorn phantom_app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

That did not solve the root cause. What it did was stop the platform from amplifying it. Sometimes the first real fix is not elegant. It is just removing the part that is making everything else harder to see.

This was also the first reminder of what Phantom Tide actually proves. Not that I can wire together a few services and make a dashboard. That I understand when architectural defaults stop being defaults and start becoming liabilities.

## The second problem: 28 MB in Redis became roughly 2 GB in Python

Once the worker count dropped, the next obvious suspect was Redis.

The live event set contained around 20,000 records. The backing JSON footprint was roughly 28 MB. That sounds harmless if you think in terms of storage size. It is not harmless if you understand what Python does to structured data once you fully materialise it into live objects.

On startup, the app was hydrating the event store by deserialising every record from the Redis sorted set and constructing dataclass instances for each one. Each `EventRecord` carried around 22 fields plus nested structures such as attributes, geometry, and raw source data. That may look compact in JSON. It is not compact in memory.

JSON is just bytes. Python objects are a managed heap full of per-object overhead, instance dictionaries, nested dictionaries, strings, references, allocator fragmentation, and garbage collector metadata. So a few dozen megabytes of stored data turned into a giant in-process object graph.

The result was approximately a 70x inflation from Redis JSON size to live heap use.

This is exactly the sort of thing that never shows up in superficial product writeups. You can talk all day about “real-time intelligence fusion,” but eventually the truth comes down to ugly details like whether your startup path is quietly reconstructing two gigabytes of Python objects because you were lazy about hydration strategy.

That was the next fix.

First I reduced retention. Then I enforced the limit at hydration time. Then I stopped eagerly materialising the entire backlog as one big in-memory list.

The retention and load limits became explicit:

```python
MAX_REDIS_EVENTS = 8_000
redis_store.load_recent_events(hours=24, limit=8_000)
ch_store.load_recent_events(hours=24, limit=8_000)
```

Live Redis was trimmed immediately so the next restart would not drag the old problem straight back in:

```sh
docker exec phantom_redis redis-cli ZREMRANGEBYRANK phantom:events 0 -8001
```

Then I changed the hydration path so it streamed records instead of building a giant list up front:

```python
def hydrate_from_redis_iter(redis_conn):
    for _, raw in redis_conn.zscan_iter('phantom:events'):
        yield EventRecord(**json.loads(raw))

def insert_streamed(client, it, chunk_size=1000):
    buffer = []
    for rec in it:
        buffer.append(rec.to_tuple())
        if len(buffer) >= chunk_size:
            client.insert('events', buffer)
            buffer.clear()
    if buffer:
        client.insert('events', buffer)
```

I also reduced per-object overhead on the hot path with slots-based dataclasses:

```python
@dataclass(slots=True)
class EventRecord:
    ...
```

That did not magically make Python cheap. It did make the startup path stop behaving like a memory ambush. Staging memray runs showed a material drop in peak usage on the hydration path after streaming and `slots=True`.

Again, this is the part most people bury because it is not glamorous. I think it is the most convincing part of the whole project. The engineering value in Phantom Tide is not that it displays events on a map. It is that it takes badly behaved, heterogeneous upstream data and forces it through a system that can be reasoned about, profiled, and corrected under production pressure.

## The third problem: the scheduler was launching a coordinated attack on startup

After reducing worker multiplication and fixing the worst of the hydration path, the platform still died.

The important clue was timing. The app would boot, sit at a few hundred megabytes, look stable, and then die exactly thirty seconds later.

Not roughly. Exactly.

That told me this was not a vague leak or gradual accumulation problem. It was a deterministic startup event.

The culprit was APScheduler.

To ensure the platform had fresh data as soon as it started, the scheduler registered one-shot startup jobs for the slower collectors before their normal intervals began. That part was fine. The bad part was that all of them were assigned the same `next_run_time`.

```python
startup_run_time = datetime.now() + timedelta(seconds=30)

for key, fn, _interval, job_id, job_name, startup_run in slow_jobs:
    collector = popped.get(key)
    if collector is not None and startup_run:
        _scheduler.add_job(
            fn,
            args=[collector],
            id=f"collectors_{job_id}_startup",
            name=f"Initial {job_name} run",
            next_run_time=startup_run_time,
        )
```

So at T+30 seconds, a whole wall of collectors hit the system simultaneously.

NDBC. MARAD. ICC-CCS. GPS advisory sources. USGS. ECCC. VIIRS. NGA MIS. DART. Multiple network fetches, parsers, object allocations, and store writes all landing at once on a constrained VM.

That is not startup. That is a deterministic burst load disguised as startup.

This is where the broader product story matters. Phantom Tide is not just “aggregating feeds.” It is a distributed argument about reality across sources that disagree, drift, stall, overproduce, and break in different ways. The engineering challenge is not collecting the signals. It is making those signals survive contact with a live system. Startup scheduling is part of that. If your collectors all fire as one synchronized burst, you have built a fragility engine, not an intelligence platform.

The fix was to introduce jitter and spread the one-shot jobs across a startup window:

```python
startup_delay = int(os.getenv("STARTUP_COLLECT_DELAY_SECONDS", "30"))
startup_window = int(os.getenv("STARTUP_COLLECT_WINDOW_SECONDS", "180"))

def _staggered_time(base_delay: int, window: int) -> datetime:
    offset = random.randint(0, max(0, window))
    return datetime.now() + timedelta(seconds=base_delay + offset)

for key, fn, _interval, job_id, job_name, startup_run in slow_jobs:
    collector = popped.get(key)
    if collector is not None and startup_run:
        _scheduler.add_job(
            fn,
            args=[collector],
            id=f"collectors_{job_id}_startup",
            name=f"Initial {job_name} run",
            next_run_time=_staggered_time(startup_delay, startup_window),
        )
```

That turned the startup profile from a cliff into a slope. Instead of thirteen collectors hitting together, they spread out over a few minutes. Memory rose gradually. The platform stayed up.

This was one of the most important fixes because it exposed a deeper truth: most real-world system failures are not a result of one dramatic bug. They come from individually reasonable choices interacting at exactly the wrong point in time.

## The fourth problem: the fast loop was still colliding with the slow startup window

The first scheduler fix removed the mass simultaneous burst. It did not fully remove startup overlap.

The fast-loop collectors still had their own initial run scheduled too early, which meant they could still collide with slow collectors that happened to land near the front of the stagger window.

So the startup sequence needed a second pass. The fast loop had to move to the end of the slow-collector window instead of overlapping with it. That changed startup from “partially staggered chaos” into an actual controlled sequence.

The rough shape became:

* application boots
* scheduler starts
* slow collectors begin after the base delay, staggered across the window
* only after that window closes does the fast-loop initial run fire

That sounds small. It was not small. It removed another artificial pressure point and made startup behave like something designed, not something improvised.

## The fifth problem: ClickHouse was configured like it owned the box

At the same time, ClickHouse was competing for memory on the same host.

That mattered because the box was shared. Phantom Tide was not running in isolation. Redis, ClickHouse, the app container, and supporting services were all drawing from the same physical machine. ClickHouse 26.2 also has opinions about startup allocations and where certain memory-related settings actually belong.

This turned into a small piece of config archaeology. Some settings were overly aggressive for the environment. Some belonged in different config scopes. Some combinations created ugly startup behaviour. One XML mistake introduced exactly the sort of pointless delay you deserve when editing config under stress.

The path out was iterative and boring in the right way:

* reduce cache sizes
* validate XML
* strip back custom config
* reintroduce only what is proven safe
* observe startup under cgroup limits
* stop treating ClickHouse like the host exists purely for it

That mattered because the platform’s strongest engineering story is not “I know how to install ClickHouse.” It is “I know how to operate a mixed system where each component lies differently under stress, and I know how to back the whole thing down to something stable without guessing.”

If you want to show engineering skill, this is where it lives. Not in saying you used ClickHouse. In showing you understand when ClickHouse becomes the wrong neighbour on a tight box unless you discipline it.

## The sixth problem: huge flushes were creating secondary memory spikes in ClickHouse

The in-memory store had another bad habit. It was flushing pending events to ClickHouse as one large batch.

That meant after a noisy restart or backlog recovery, the first insert could be enormous. ClickHouse would then need to process that insert in memory before writing it out, which is exactly the kind of thing you do not want happening on a machine already recovering from pressure.

Before, it effectively looked like this:

```python
ch_store.insert_events(batch)
```

That is fine until `batch` is not fine.

So I chunked it:

```python
_CH_FLUSH_CHUNK = 2_000

for i in range(0, len(batch), _CH_FLUSH_CHUNK):
    chunk = batch[i:i + _CH_FLUSH_CHUNK]
    ch_store.insert_events(chunk)
```

That bounded per-insert memory pressure and made recovery behaviour much more predictable.

That kind of change matters more than people think. Predictability is one of the few real luxuries you can buy in production. Large single-shot flushes feel efficient until they are the thing that tips a struggling system over the edge.

## The seventh problem: zero swap headroom made every spike fatal

The container limits were also too sharp.

The app had effectively no swap breathing room:

```yaml
mem_limit: 2g
memswap_limit: 2g
```

That means any transient spike above 2 GB becomes an immediate death sentence. For a service with a rough startup path and bursty collector behaviour, that is needlessly unforgiving.

Once the real fixes were in place, I widened the operating margin:

```yaml
mem_limit: 4g
memswap_limit: 5g
```

This did not replace proper engineering. It complemented it. There is a difference between using headroom to hide a bad design and using headroom to stop temporary spikes from killing an otherwise stabilised service. This was the latter.

## What changed after the fixes

After the worker reduction, Redis cap, streamed hydration, scheduler staggering, fast-loop sequencing, ClickHouse insert chunking, conservative ClickHouse tuning, and memory headroom adjustments, the platform stopped behaving like a brittle prototype and started behaving like an actual system.

The important thing was not just that it stopped crashing. It was how it stopped crashing.

Before:

* startup looked normal and then detonated
* all collectors behaved like they had no awareness of each other
* Redis hydration inflated into a giant Python heap
* ClickHouse was competing too aggressively for memory
* one large persistence flush could create another spike
* the container limits gave no room for transient pressure

After:

* startup memory climbed gradually instead of cliffing
* collectors came online in a controlled sequence
* hydration was bounded and streamed
* ClickHouse stopped acting like it owned the host
* flush behaviour became predictable
* the app settled into a sane steady-state range

That is the real engineering story of Phantom Tide. Not that it fuses AIS, OpenSky, NOTAMs, GPS interference, advisories, marine feeds, and other operational sources into one view. The stronger claim is that it does that while surviving contact with production realities that kill weaker systems.

## What this incident proved about the product

This outage ended up clarifying the product better than any launch copy could have.

I had been tempted, like everyone is, to talk about Phantom Tide as a live map or an intelligence interface. That is the easy description. It is also the shallow one.

The deeper and more defensible framing is this:

Phantom Tide is not a dashboard. It is a systems engineering case study disguised as an intelligence platform.

The difficult part is not rendering events. The difficult part is deciding what deserves to become an event in the first place, how long it should live, how it should be structured, how conflicting sources should coexist, how startup should behave, how persistence should fail safely, and how the platform should degrade under pressure without becoming fiction.

That is what the OOM incident surfaced. The value is not the glossy layer. It is the logic and discipline beneath it.

A year from now, the thing I would regret most is underselling that by talking too much about the output and not enough about the machinery. The map is useful because the platform behind it earned the right to produce it. That is the part worth showing.

## The uncomfortable truth

If I marketed Phantom Tide mainly as “a live map that merges these sources,” a lot of technically serious people would underestimate it instantly.

They would assume the hard part was UI composition and data plumbing. They would file it mentally under dashboard-builder. They would miss the actual signal: scheduler design, source reconciliation, object inflation, memory profiling, batch persistence strategy, cache-vs-archive reasoning, and live operational debugging under constrained infrastructure.

That is why I think the mess is the moat.

Not the mess in the sense of sloppy engineering. The mess in the sense of the real problems you only meet when a system is no longer theoretical. Bad upstreams. Structural drift. startup stampedes. false health. silent data loss. stateful assumptions hiding inside supposedly simple services. Those are not embarrassing side notes. They are the proof of contact with reality.

Anyone can make a pretty interface over commodity data. Very few people can explain why 28 MB in Redis became 2 GB in Python, why four workers made the system worse, why startup jitter mattered more than another CPU, why ClickHouse needed discipline, and why archival persistence was still the next priority even after the platform looked stable again.

That is the engineering skill. That is what Phantom Tide really demonstrates.

## What still remains

Fixing the OOM loop did not mean the platform was finished.

The highest-priority remaining issue is ClickHouse insert failure caused by malformed field types. At least one collector is emitting a `dict` where ClickHouse expects a string or numeric field, which poisons entire insert batches. The in-memory store and Redis make the platform look healthy in the short term, but the archive path is not trustworthy until there is schema validation at the boundary.

That is the next real job:

* validate per-event payloads before persistence
* log the source and field causing schema failures
* coerce where appropriate
* reject where necessary
* stop silent data loss from hiding behind a healthy-looking UI

There are other source-specific issues as well, but those are normal platform work. The insert validation gap is the big one because it attacks trust in the archive.

## The real lesson

The kernel told the truth first.

Everything else was just me catching up to it.

This was not one bug. It was a layered systems failure where worker topology, object modelling, startup choreography, batch behaviour, database configuration, and memory limits all interacted in exactly the wrong way. The platform was not failing because of a single bad line of code. It was failing because multiple “reasonable” decisions had combined into a design that only looked solid until production put pressure on it.

That is why I think this incident matters.

Not because the site went down. Systems go down.

It matters because it exposed what Phantom Tide actually is: not a map, not a feed aggregator, not a dressed-up frontend project, but a live operational system built on top of messy, high-friction data, where the hardest work is imposing structure, discipline, and survivability on things that do not want to behave.

That is the engineering story.

And that is the part worth selling.
