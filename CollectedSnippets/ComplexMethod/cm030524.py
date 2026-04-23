def _handle_run(args):
    """Handle the 'run' command."""
    # Validate target exists before launching subprocess
    if args.module:
        # Temporarily add cwd to sys.path so we can find modules in the
        # current directory, matching the coordinator's behavior
        cwd = os.getcwd()
        added_cwd = False
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
            added_cwd = True
        try:
            if importlib.util.find_spec(args.target) is None:
                raise SamplingModuleNotFoundError(args.target)
        finally:
            if added_cwd:
                sys.path.remove(cwd)
    else:
        if not os.path.exists(args.target):
            raise SamplingScriptNotFoundError(args.target)

    # Check if live mode is requested
    if args.live:
        _handle_live_run(args)
        return

    # Build the command to run
    if args.module:
        cmd = (sys.executable, "-m", args.target, *args.args)
    else:
        cmd = (sys.executable, args.target, *args.args)

    # Run with synchronization
    try:
        process = _run_with_sync(cmd, suppress_output=False)
    except RuntimeError as e:
        sys.exit(f"Error: {e}")

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
        output_file = args.outfile or _generate_output_filename(args.format, process.pid)

    # Create the appropriate collector
    collector = _create_collector(
        args.format, args.sample_interval_usec, skip_idle, args.opcodes,
        output_file=output_file,
        compression=getattr(args, 'compression', 'auto'),
        diff_baseline=args.diff_baseline
    )

    with _get_child_monitor_context(args, process.pid):
        try:
            collector = sample(
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
            _handle_output(collector, args, process.pid, mode)
        finally:
            # Terminate the main subprocess - child profilers finish when their
            # target processes exit
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=_PROCESS_KILL_TIMEOUT_SEC)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()