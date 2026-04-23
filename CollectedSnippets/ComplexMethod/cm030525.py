def _handle_live_run(args):
    """Handle live mode for running a script/module."""
    # Build the command to run
    if args.module:
        cmd = (sys.executable, "-m", args.target, *args.args)
    else:
        cmd = (sys.executable, args.target, *args.args)

    # Run with synchronization, suppressing output for live mode
    try:
        process = _run_with_sync(cmd, suppress_output=True)
    except RuntimeError as e:
        sys.exit(f"Error: {e}")

    mode = _parse_mode(args.mode)

    # Determine skip_idle based on mode
    skip_idle = mode != PROFILING_MODE_WALL

    # Create live collector with default settings
    collector = LiveStatsCollector(
        args.sample_interval_usec,
        skip_idle=skip_idle,
        sort_by="tottime",  # Default initial sort
        limit=20,  # Default limit
        pid=process.pid,
        mode=mode,
        opcodes=args.opcodes,
        async_aware=args.async_mode if args.async_aware else None,
    )

    # Profile the subprocess in live mode
    try:
        sample_live(
            process.pid,
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
    finally:
        # Clean up the subprocess and get any error output
        returncode = process.poll()
        if returncode is None:
            # Process still running - terminate it
            process.terminate()
            try:
                process.wait(timeout=_PROCESS_KILL_TIMEOUT_SEC)
            except subprocess.TimeoutExpired:
                process.kill()
        # Ensure process is fully terminated
        process.wait()
        # Read any stderr output (tracebacks, errors, etc.)
        if process.stderr:
            with process.stderr:
                try:
                    stderr = process.stderr.read()
                    if stderr:
                        print(stderr.decode(), file=sys.stderr)
                except (OSError, ValueError):
                    # Ignore errors if pipe is already closed
                    pass