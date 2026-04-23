def _handle_output(collector, args, pid, mode):
    """Handle output for the collector based on format and arguments.

    Args:
        collector: The collector instance with profiling data
        args: Parsed command-line arguments
        pid: Process ID (for generating filenames)
        mode: Profiling mode used
    """
    if args.format == "binary":
        # Binary format already wrote to file incrementally, just finalize
        collector.export(None)
        filename = collector.filename
        print(f"Binary profile written to {filename} ({collector.total_samples} samples)")
    elif args.format == "pstats":
        if args.outfile:
            # If outfile is a directory, generate filename inside it
            if os.path.isdir(args.outfile):
                filename = os.path.join(args.outfile, _generate_output_filename(args.format, pid))
                collector.export(filename)
            else:
                collector.export(args.outfile)
        else:
            # Print to stdout with defaults applied
            sort_choice = args.sort if args.sort is not None else "nsamples"
            limit = args.limit if args.limit is not None else 15
            sort_mode = _sort_to_mode(sort_choice)
            collector.print_stats(
                sort_mode, limit, not args.no_summary, mode
            )
    else:
        # Export to file
        if args.outfile and os.path.isdir(args.outfile):
            # If outfile is a directory, generate filename inside it
            filename = os.path.join(args.outfile, _generate_output_filename(args.format, pid))
        else:
            filename = args.outfile or _generate_output_filename(args.format, pid)
        collector.export(filename)

        # Auto-open browser for HTML output if --browser flag is set
        if args.format in ('flamegraph', 'diff_flamegraph', 'heatmap') and getattr(args, 'browser', False):
            _open_in_browser(filename)