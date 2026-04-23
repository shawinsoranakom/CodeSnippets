def _check_stream_sync_overlap(events: list[dict]) -> list[Violation]:
    """For each Stream Synchronize on (device, stream), no kernel on that
    stream should still be running when the sync starts."""
    stream_syncs = []
    for ev in events:
        if (
            ev.get("ph") == "X"
            and ev.get("cat") == "cuda_sync"
            and ev.get("args", {}).get("cuda_sync_kind") == "Stream Sync"
        ):
            args = ev.get("args", {})
            stream_syncs.append(
                {
                    "ts": float(ev.get("ts", 0)),
                    "dur": float(ev.get("dur", 0)),
                    "stream": args.get("stream"),
                    "device": args.get("device"),
                }
            )
    if not stream_syncs:
        return []

    kernels_by_stream: dict[tuple, list[dict]] = defaultdict(list)
    for ev in events:
        if ev.get("ph") == "X" and ev.get("cat") == "kernel":
            args = ev.get("args", {})
            key = (args.get("device"), args.get("stream"))
            ts = float(ev.get("ts", 0))
            kernels_by_stream[key].append(
                {
                    "ts": ts,
                    "end": ts + float(ev.get("dur", 0)),
                    "name": ev.get("name", ""),
                }
            )

    violations = []
    for sync in stream_syncs:
        key = (sync["device"], sync["stream"])
        for k in kernels_by_stream.get(key, []):
            if k["ts"] < sync["ts"] < k["end"]:
                overlap = k["end"] - sync["ts"]
                violations.append(
                    Violation(
                        rule_name="_check_stream_sync_overlap",
                        message=(
                            f"StreamSynchronize on device={sync['device']} "
                            f"stream={sync['stream']} at ts={sync['ts']:.1f}us "
                            f"but kernel '{k['name']}' (ends {k['end']:.1f}us) "
                            f"is still running ({overlap:.1f}us overlap)"
                        ),
                    )
                )
    return violations