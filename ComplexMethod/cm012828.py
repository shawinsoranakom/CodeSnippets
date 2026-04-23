def _group_events_per_cta_occupancy(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Process warp events into CTA-level events with slot assignment.

    Each CTA gets: min warp start, max warp end.
    CTAs are assigned to slots per SM such that non-overlapping CTAs share slots.
    """
    core_cta_pattern = re.compile(r"^(.*?)\s*(Core\d+)\s+(CTA\d+)$")

    # Group events by (prefix, SM, CTA)
    cta_events: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for event in events:
        pid = event.get("pid", "")
        match = core_cta_pattern.match(str(pid))
        if match:
            prefix = match.group(1).strip()
            core = match.group(2)
            cta = match.group(3)
            key = (prefix, core, cta)
            if key not in cta_events:
                cta_events[key] = []
            cta_events[key].append(event)

    # For each CTA, compute min start and max end
    cta_intervals: dict[tuple[str, str, str], tuple[float, float]] = {}
    for key, evts in cta_events.items():
        min_start = float("inf")
        max_end = float("-inf")
        for evt in evts:
            ts = evt.get("ts", 0)
            dur = evt.get("dur", 0)
            min_start = min(min_start, ts)
            max_end = max(max_end, ts + dur)
        if min_start != float("inf"):
            cta_intervals[key] = (min_start, max_end)

    # Group CTAs by (prefix, SM) and assign to slots
    sm_ctas: dict[tuple[str, str], list[tuple[str, float, float]]] = {}
    for (prefix, core, cta), (start, end) in cta_intervals.items():
        sm_key = (prefix, core)
        if sm_key not in sm_ctas:
            sm_ctas[sm_key] = []
        sm_ctas[sm_key].append((cta, start, end))

    # Assign CTAs to slots using interval scheduling (greedy)
    cta_slot_assignments: dict[tuple[str, str, str], int] = {}
    for sm_key, ctas in sm_ctas.items():
        prefix, core = sm_key
        sorted_ctas = sorted(ctas, key=lambda x: x[1])
        slots: list[float] = []
        for cta, start, end in sorted_ctas:
            assigned_slot = None
            for i, slot_end in enumerate(slots):
                if start >= slot_end:
                    assigned_slot = i
                    slots[i] = end
                    break
            if assigned_slot is None:
                assigned_slot = len(slots)
                slots.append(end)
            cta_slot_assignments[(prefix, core, cta)] = assigned_slot

    # Build numeric ID mappings for pids and tids
    # Chrome trace format requires numeric pid/tid values
    pid_names: dict[str, int] = {}
    tid_names: dict[tuple[int, str], int] = {}  # (pid, tid_name) -> tid_num

    for key in cta_intervals:
        prefix, core, cta = key
        pid_name = f"{prefix} {core}" if prefix else core
        if pid_name not in pid_names:
            pid_names[pid_name] = len(pid_names)

    new_events: list[dict[str, Any]] = []

    # Add process name metadata events
    for pid_name, pid_num in pid_names.items():
        new_events.append(
            {
                "name": "process_name",
                "ph": "M",
                "pid": pid_num,
                "args": {"name": pid_name},
            }
        )

    # Create CTA events with numeric IDs and collect tid mappings
    for key, (start, end) in cta_intervals.items():
        prefix, core, cta = key
        slot = cta_slot_assignments[key]
        pid_name = f"{prefix} {core}" if prefix else core
        tid_name = f"slot{slot}"
        pid_num = pid_names[pid_name]

        if (pid_num, tid_name) not in tid_names:
            tid_num = len(tid_names)
            tid_names[(pid_num, tid_name)] = tid_num
            # Add thread name metadata event
            new_events.append(
                {
                    "name": "thread_name",
                    "ph": "M",
                    "pid": pid_num,
                    "tid": tid_num,
                    "args": {"name": tid_name},
                }
            )
        else:
            tid_num = tid_names[(pid_num, tid_name)]

        new_events.append(
            {
                "name": cta,
                "cat": "cta",
                "ph": "X",
                "ts": start,
                "dur": end - start,
                "pid": pid_num,
                "tid": tid_num,
            }
        )

    return new_events