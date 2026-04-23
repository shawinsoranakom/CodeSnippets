def process_proton_trace(
    trace_path: str,
    output_dir: str | None = None,
    group_by_sm: bool = True,
    split_invocations: bool = True,
    scale_factor: float = 1.0,
    gap_threshold_ns: float = 1000.0,
    per_cta_occupancy: bool = True,
) -> list[str]:
    """
    Process a proton trace file with various transformations.

    Always produces 1 + N files: one complete trace and N per-invocation traces.
    Grouping options (group_by_sm, per_cta_occupancy) apply uniformly to all outputs.

    Args:
        trace_path: Path to the input Chrome trace file
        output_dir: Directory to write output files. If None, uses same directory as input.
        group_by_sm: If True, group CTAs by SM into single tracks.
        split_invocations: If True, also produce per-invocation trace files.
        scale_factor: Factor to scale durations by (helps visibility in Perfetto).
        gap_threshold_ns: Time gap (in nanoseconds) that indicates a new invocation.
        per_cta_occupancy: If True, process warp tracks into CTA tracks and assign
            CTAs to slots per SM such that CTAs do not overlap.

    Returns:
        List of paths to the output files.
    """
    if output_dir is None:
        output_dir = os.path.dirname(trace_path) or "."

    os.makedirs(output_dir, exist_ok=True)
    base_name = _get_base_name(trace_path)

    data = _read_trace(trace_path)
    events = data.get("traceEvents", [])

    # Split into invocations first (before grouping, to avoid merging across invocations)
    invocations = _split_events_by_invocation(events, gap_threshold_ns)

    # Apply grouping transformation to each invocation
    invocations = [
        _apply_grouping(inv_events, group_by_sm, per_cta_occupancy)
        for inv_events in invocations
    ]

    output_files = []

    # Write complete trace (dedupe metadata events)
    complete_events = []
    seen_metadata: OrderedSet[tuple[str | None, int | None, int | None]] = OrderedSet()
    for inv_events in invocations:
        for event in inv_events:
            if event.get("ph") == "M":
                # Dedupe metadata events by (name, pid, tid)
                key = (event.get("name"), event.get("pid"), event.get("tid"))
                if key in seen_metadata:
                    continue
                seen_metadata.add(key)
            complete_events.append(event)
    complete_path = os.path.join(output_dir, f"{base_name}.trace.json.gz")
    _write_trace(complete_path, {"traceEvents": complete_events})
    output_files.append(complete_path)

    # Write per-invocation traces
    if split_invocations:
        for i, inv_events in enumerate(invocations):
            inv_events = _normalize_timestamps(list(inv_events), scale_factor)
            inv_path = os.path.join(
                output_dir, f"{base_name}_invocation_{i}.trace.json.gz"
            )
            _write_trace(inv_path, {"traceEvents": inv_events})
            output_files.append(inv_path)

    return output_files