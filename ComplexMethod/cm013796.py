def _check_stream_wait_corr_id_in_past(events: list[dict]) -> list[Violation]:
    """wait_on_cuda_event_record_corr_id must point to a cudaEventRecord
    with cudaEventRecord.ts <= stream_wait.ts."""
    event_record_ts: dict[int, float] = {}
    for ev in events:
        if (
            ev.get("ph") == "X"
            and ev.get("cat") in ("cuda_runtime", "cuda_driver")
            and ev.get("name") in _CUDA_EVENT_RECORD_NAMES
        ):
            args = ev.get("args", {})
            ts = float(ev.get("ts", 0))
            for field in ("External id", "correlation"):
                cid = args.get(field)
                if cid is not None:
                    cid = int(cid)
                    if cid not in event_record_ts or ts < event_record_ts[cid]:
                        event_record_ts[cid] = ts

    violations = []
    for ev in events:
        if ev.get("ph") != "X":
            continue
        args = ev.get("args", {})
        if args.get("cuda_sync_kind") != "Stream Wait Event":
            continue
        ref = args.get("wait_on_cuda_event_record_corr_id")
        if ref is None or int(ref) < 0:
            continue
        ref = int(ref)
        sw_ts = float(ev.get("ts", 0))
        record_ts = event_record_ts.get(ref)

        if record_ts is None:
            violations.append(
                Violation(
                    rule_name="_check_stream_wait_corr_id_in_past",
                    message=(
                        f"Stream Wait Event at ts={sw_ts:.1f}us references "
                        f"corr_id={ref} but no matching cudaEventRecord in trace"
                    ),
                )
            )
        elif record_ts > sw_ts:
            lag = record_ts - sw_ts
            violations.append(
                Violation(
                    rule_name="_check_stream_wait_corr_id_in_past",
                    message=(
                        f"Stream Wait Event at ts={sw_ts:.1f}us references "
                        f"cudaEventRecord (corr_id={ref}) {lag:.1f}us in the future "
                        f"(event_record_ts={record_ts:.1f})"
                    ),
                )
            )
    return violations