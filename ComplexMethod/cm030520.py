def _replay_with_reader(args, reader):
    """Replay samples from an open binary reader."""
    info = reader.get_info()
    interval = info['sample_interval_us']

    print(f"Replaying {info['sample_count']} samples from {args.input_file}")
    print(f"  Sample interval: {interval} us")
    print(
        "  Compression: "
        f"{'zstd' if info.get('compression_type', 0) == 1 else 'none'}"
    )

    collector = _create_collector(
        args.format, interval, skip_idle=False,
        diff_baseline=args.diff_baseline
    )

    def progress_callback(current, total):
        if total > 0:
            pct = current / total
            bar_width = 40
            filled = int(bar_width * pct)
            bar = '█' * filled + '░' * (bar_width - filled)
            print(
                f"\r  [{bar}] {pct*100:5.1f}% ({current:,}/{total:,})",
                end="",
                flush=True,
            )

    count = reader.replay_samples(collector, progress_callback)
    print()

    if args.format == "pstats":
        if args.outfile:
            collector.export(args.outfile)
        else:
            sort_choice = (
                args.sort if args.sort is not None else "nsamples"
            )
            limit = args.limit if args.limit is not None else 15
            sort_mode = _sort_to_mode(sort_choice)
            collector.print_stats(
                sort_mode, limit, not args.no_summary,
                PROFILING_MODE_WALL
            )
    else:
        filename = (
            args.outfile
            or _generate_output_filename(args.format, os.getpid())
        )
        collector.export(filename)

        # Auto-open browser for HTML output if --browser flag is set
        if (
            args.format in (
                'flamegraph', 'diff_flamegraph', 'heatmap'
            )
            and getattr(args, 'browser', False)
        ):
            _open_in_browser(filename)

    print(f"Replayed {count} samples")