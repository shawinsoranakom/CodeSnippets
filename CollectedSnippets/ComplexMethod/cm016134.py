def filter_perf(all_perf: list[PerfData], args) -> list[PerfData]:
    result = all_perf
    if getattr(args, "config", None):
        pattern = re.compile(args.config, re.IGNORECASE)
        result = [p for p in result if pattern.search(p.config)]
    if getattr(args, "suite", None):
        suite = SUITE_ALIASES.get(args.suite, args.suite)
        result = [p for p in result if p.suite == suite]
    if getattr(args, "mode", None):
        result = [p for p in result if p.mode == args.mode]
    if getattr(args, "backend", None):
        pattern = re.compile(args.backend, re.IGNORECASE)
        result = [p for p in result if pattern.search(p.short_name)]
    if getattr(args, "dtype", None):
        result = [p for p in result if p.dtype == args.dtype]
    if getattr(args, "runtime", None):
        result = [p for p in result if p.runtime == args.runtime]
    return result