def annotate_trace(
    trace: dict,
    annotations: dict[int, list[Any]],
    default_stream: int = 7,
) -> int:
    """Add annotation fields to kernel events matching the annotations dict.

    Each annotation entry is a list (from nested ``mark_kernels`` scopes).
    Fields from all annotations are merged into the event args; if multiple
    annotations define the same key, later entries in the list win.

    For graphed events (graph_node_id != 0), reassigns ``tid`` and
    ``args["stream"]`` to the stream recorded in annotations, or to
    *default_stream* if there is no annotation.  Also moves the
    corresponding ``ac2g`` flow-finish events to the new tid so that
    CPU-to-GPU correlation arrows are preserved.

    Removes ``gpu_user_annotation`` events and orphaned ``ac2g`` events
    from streams that have no kernel or memcpy events after reassignment,
    since CUPTI replicates these onto every stream during graph replay.

    Returns the number of events annotated.
    """
    # Build an index of ac2g 'f' events keyed by (tid, ts) so we can
    # move them together with the kernel events they correspond to.
    ac2g_f_index: dict[tuple, list] = {}
    for event in trace["traceEvents"]:
        if event.get("cat") == "ac2g" and event.get("ph") == "f":
            key = (event.get("tid"), event.get("ts"))
            ac2g_f_index.setdefault(key, []).append(event)

    annotated = 0
    for event in trace.get("traceEvents", []):
        args = event.get("args", {})
        graph_node_id = args.get("graph node id")
        if graph_node_id is None or graph_node_id == 0:
            continue
        stream_id = None
        if graph_node_id in annotations:
            for ann in annotations[graph_node_id]:
                if isinstance(ann, dict):
                    for key, value in ann.items():
                        args[key] = str(value)
                    if "stream" in ann:
                        stream_id = int(ann["stream"])
                else:
                    args["annotation"] = str(ann)
            annotated += 1

        # Reassign stream: use annotated stream if available, else default
        if stream_id is None:
            stream_id = default_stream
        old_key = (event.get("tid"), event.get("ts"))
        event["tid"] = stream_id
        args["stream"] = stream_id

        # Move the matching ac2g 'f' event(s) to the same new tid
        for ac2g_event in ac2g_f_index.get(old_key, ()):
            ac2g_event["tid"] = stream_id

    # Remove gpu_user_annotation events and ac2g flow-finish events from
    # streams that have no real kernel/memcpy/memset work -- these are
    # noise replicated by CUPTI onto every stream during graph replay.
    tids_with_work = set()
    for event in trace["traceEvents"]:
        if event.get("cat") in _WORK_CATEGORIES:
            tids_with_work.add(event.get("tid"))

    def _is_noise(event: dict) -> bool:
        cat = event.get("cat")
        if cat == "gpu_user_annotation":
            return event.get("tid") not in tids_with_work
        if cat == "ac2g" and event.get("ph") == "f":
            return event.get("tid") not in tids_with_work
        return False

    original_count = len(trace["traceEvents"])
    trace["traceEvents"] = [
        event for event in trace["traceEvents"] if not _is_noise(event)
    ]
    removed = original_count - len(trace["traceEvents"])
    if removed:
        print(f"Removed {removed} noise events from empty streams")

    # Clean up metadata: remove thread_name / thread_sort_index entries
    # for noise streams that have no real (non-metadata) events, and add
    # thread_name entries for our new annotation streams.
    all_tids_in_trace = {
        e.get("tid") for e in trace["traceEvents"] if e.get("ph") != "M"
    }
    # Find the GPU process pid from existing thread_name metadata
    gpu_pid = 0
    for event in trace["traceEvents"]:
        if (
            event.get("ph") == "M"
            and event.get("name") == "thread_name"
            and str(event.get("args", {}).get("name", "")).startswith("stream ")
        ):
            gpu_pid = event.get("pid", 0)
            break

    # Remove metadata entries for tids with no non-metadata events
    trace["traceEvents"] = [
        event
        for event in trace["traceEvents"]
        if event.get("ph") != "M" or event.get("tid") in all_tids_in_trace
    ]

    # Add thread_name metadata for new annotation tids that lack one
    existing_thread_names = {
        e.get("tid")
        for e in trace["traceEvents"]
        if e.get("ph") == "M" and e.get("name") == "thread_name"
    }
    for tid in sorted(tids_with_work - existing_thread_names):
        trace["traceEvents"].append(
            {
                "ph": "M",
                "pid": gpu_pid,
                "tid": tid,
                "name": "thread_name",
                "args": {"name": f"stream {tid}"},
            }
        )

    return annotated