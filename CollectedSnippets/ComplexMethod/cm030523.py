def _handle_attach(args):
    """Handle the 'attach' command."""
    if not _is_process_running(args.pid):
        raise SamplingUnknownProcessError(args.pid)
    # Check if live mode is requested
    if args.live:
        _handle_live_attach(args, args.pid)
        return

    # Use PROFILING_MODE_ALL for gecko format
    mode = (
        PROFILING_MODE_ALL
        if args.format == "gecko"
        else _parse_mode(args.mode)
    )

    # Determine skip_idle based on mode
    skip_idle = (
        mode != PROFILING_MODE_WALL if mode != PROFILING_MODE_ALL else False
    )

    output_file = None
    if args.format == "binary":
        output_file = args.outfile or _generate_output_filename(args.format, args.pid)

    # Create the appropriate collector
    collector = _create_collector(
        args.format, args.sample_interval_usec, skip_idle, args.opcodes,
        output_file=output_file,
        compression=getattr(args, 'compression', 'auto'),
        diff_baseline=args.diff_baseline
    )

    with _get_child_monitor_context(args, args.pid):
        collector = sample(
            args.pid,
            collector,
            duration_sec=args.duration,
            all_threads=args.all_threads,
            realtime_stats=args.realtime_stats,
            mode=mode,
            async_aware=args.async_mode if args.async_aware else None,
            native=args.native,
            gc=args.gc,
            opcodes=args.opcodes,
            blocking=args.blocking,
        )
        _handle_output(collector, args, args.pid, mode)