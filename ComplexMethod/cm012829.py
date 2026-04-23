def _normalize_timestamps(
    events: list[dict[str, Any]], scale_factor: float = 1.0
) -> list[dict[str, Any]]:
    """Normalize timestamps to start at 0 and optionally scale."""
    if not events:
        return events

    # Only consider duration events (ph=X) for min timestamp calculation
    duration_events = [e for e in events if e.get("ph") == "X"]
    if not duration_events:
        return events

    min_ts = min(e.get("ts", 0) for e in duration_events)
    for event in events:
        if event.get("ph") == "X":
            event["ts"] = (event.get("ts", 0) - min_ts) * scale_factor
            if "dur" in event:
                event["dur"] = event["dur"] * scale_factor

    return events