def _augment_memory_snapshot_stack_traces(
    snapshot: str | _Snapshot,
) -> _Snapshot:
    """
    Augment a memory snapshot with original source stack traces from FX metadata.

    IMPORTANT: This function reads from a global in-memory registry (_FX_METADATA_REGISTRY)
    that is populated during graph module compilation. It must be called in the same
    Python process where the FX graphs were compiled. It cannot be used to augment
    snapshots loaded from disk in a different process.

    Args:
        snapshot (str or _Snapshot): Either a memory snapshot dict or path to a snapshot pickle file

    Returns:
        _Snapshot: The augmented snapshot dictionary with fx_node_op, fx_node_name,
            fx_original_trace, and fx_node_info fields added to frames
    """

    snapshot_dict: _Snapshot
    if isinstance(snapshot, str):
        # Load the memory snapshot
        with open(snapshot, "rb") as f:
            snapshot_dict = cast(_Snapshot, pickle.load(f))
    else:
        snapshot_dict = snapshot

    # Process blocks in segments (for regular allocations)
    for segment in snapshot_dict.get("segments", []):
        for block in segment.get("blocks", []):
            if "frames" in block:
                _augment_frames(block["frames"])

    # Process device traces (for memory history)
    for trace_list in snapshot_dict.get("device_traces", []):
        for trace_entry in trace_list:
            if isinstance(trace_entry, dict) and "frames" in trace_entry:
                _augment_frames(trace_entry["frames"])

    return snapshot_dict