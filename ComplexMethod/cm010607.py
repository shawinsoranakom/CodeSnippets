def _fix_overlapping_timestamps(trace: dict, max_adjust_us: float = 1.0) -> int:
    """Clamp graphed kernel/memcpy timestamps so they don't overlap on the same stream.

    CUPTI can produce slightly overlapping timestamps for consecutive graphed
    events, causing Perfetto to hide events that sit entirely "under" their
    neighbours.  This pass sorts graphed work events per stream and ensures
    each event starts at or after the previous event's end.

    Overlaps larger than *max_adjust_us* are flagged as warnings and left
    unchanged, since they likely indicate a real issue rather than CUPTI
    timestamp jitter.

    Returns the number of events adjusted.
    """
    per_stream: dict[int, list[dict]] = defaultdict(list)
    for event in trace["traceEvents"]:
        if (
            event.get("cat") in _WORK_CATEGORIES
            and event.get("args", {}).get("graph node id", 0) != 0
        ):
            per_stream[event.get("tid")].append(event)

    adjusted = 0
    for tid, events in per_stream.items():
        events.sort(key=lambda e: e["ts"])
        prev_end = 0.0
        for event in events:
            ts = event["ts"]
            dur = event.get("dur", 0)
            if ts < prev_end:
                overlap = prev_end - ts
                if overlap > max_adjust_us:
                    print(
                        f"WARNING: large overlap {overlap:.3f}us on stream {tid} "
                        f"for {event.get('name', '?')[:60]}, skipping adjustment"
                    )
                else:
                    event["ts"] = prev_end
                    adjusted += 1
            prev_end = event["ts"] + dur

    return adjusted