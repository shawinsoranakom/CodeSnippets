def _validate_args(args, parser):
    """Validate format-specific options and live mode requirements.

    Args:
        args: Parsed command-line arguments
        parser: ArgumentParser instance for error reporting
    """
    # Replay command has no special validation needed
    if getattr(args, 'command', None) == "replay":
        return

    # Warn about blocking mode with aggressive sampling intervals
    if args.blocking and args.sample_interval_usec < 100:
        print(
            f"Warning: --blocking with a {args.sample_interval_usec} µs interval will stop all threads "
            f"{1_000_000 // args.sample_interval_usec} times per second. "
            "Consider using --sampling-rate 1khz or lower to reduce overhead.",
            file=sys.stderr
        )

    # Check if live mode is available
    if hasattr(args, 'live') and args.live and LiveStatsCollector is None:
        parser.error(
            "Live mode requires the curses module, which is not available."
        )

    # --subprocesses is incompatible with --live
    if hasattr(args, 'subprocesses') and args.subprocesses:
        if ChildProcessMonitor is None:
            parser.error(
                "--subprocesses is not available on this platform "
                "(requires _remote_debugging module)."
            )
        if hasattr(args, 'live') and args.live:
            parser.error("--subprocesses is incompatible with --live mode.")

    # Async-aware mode is incompatible with --native, --no-gc, --mode, and --all-threads
    if getattr(args, 'async_aware', False):
        issues = []
        if args.native:
            issues.append("--native")
        if not args.gc:
            issues.append("--no-gc")
        if hasattr(args, 'mode') and args.mode != "wall":
            issues.append(f"--mode={args.mode}")
        if hasattr(args, 'all_threads') and args.all_threads:
            issues.append("--all-threads")
        if issues:
            parser.error(
                f"Options {', '.join(issues)} are incompatible with --async-aware. "
                "Async-aware profiling uses task-based stack reconstruction."
            )

    # --async-mode requires --async-aware
    if hasattr(args, 'async_mode') and args.async_mode != "running" and not getattr(args, 'async_aware', False):
        parser.error("--async-mode requires --async-aware to be enabled.")

    # Live mode is incompatible with format options
    if hasattr(args, 'live') and args.live:
        if args.format != "pstats":
            format_flag = f"--{args.format}"
            parser.error(
                f"--live is incompatible with {format_flag}. Live mode uses a TUI interface."
            )

        # Live mode is also incompatible with pstats-specific options
        issues = []
        if args.sort is not None:
            issues.append("--sort")
        if args.limit is not None:
            issues.append("--limit")
        if args.no_summary:
            issues.append("--no-summary")

        if issues:
            parser.error(
                f"Options {', '.join(issues)} are incompatible with --live. "
                "Live mode uses a TUI interface with its own controls."
            )
        return

    # Validate gecko mode doesn't use non-wall mode
    if args.format == "gecko" and getattr(args, 'mode', 'wall') != "wall":
        parser.error(
            "--mode option is incompatible with --gecko. "
            "Gecko format automatically includes both GIL-holding and CPU status analysis."
        )

    # Validate --opcodes is only used with compatible formats
    opcodes_compatible_formats = ("live", "gecko", "flamegraph", "diff_flamegraph", "heatmap", "binary")
    if getattr(args, 'opcodes', False) and args.format not in opcodes_compatible_formats:
        parser.error(
            f"--opcodes is only compatible with {', '.join('--' + f for f in opcodes_compatible_formats)}."
        )

    # Validate pstats-specific options are only used with pstats format
    if args.format != "pstats":
        issues = []
        if args.sort is not None:
            issues.append("--sort")
        if args.limit is not None:
            issues.append("--limit")
        if args.no_summary:
            issues.append("--no-summary")

        if issues:
            format_flag = f"--{args.format}"
            parser.error(
                f"Options {', '.join(issues)} are only valid with --pstats, not {format_flag}"
            )