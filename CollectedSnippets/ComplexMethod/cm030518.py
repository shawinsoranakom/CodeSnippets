def _build_child_profiler_args(args):
    child_args = []

    # Sampling options
    hz = MICROSECONDS_PER_SECOND // args.sample_interval_usec
    child_args.extend(["-r", str(hz)])
    if args.duration is not None:
        child_args.extend(["-d", str(args.duration)])
    if args.all_threads:
        child_args.append("-a")
    if args.realtime_stats:
        child_args.append("--realtime-stats")
    if args.native:
        child_args.append("--native")
    if not args.gc:
        child_args.append("--no-gc")
    if args.opcodes:
        child_args.append("--opcodes")
    if args.async_aware:
        child_args.append("--async-aware")
        async_mode = getattr(args, 'async_mode', 'running')
        if async_mode != "running":
            child_args.extend(["--async-mode", async_mode])

    # Mode options
    mode = getattr(args, 'mode', 'wall')
    if mode != "wall":
        child_args.extend(["--mode", mode])

    # Format options (skip pstats as it's the default)
    if args.format != "pstats":
        child_args.append(f"--{args.format}")

    return child_args