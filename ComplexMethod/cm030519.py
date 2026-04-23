def _create_collector(format_type, sample_interval_usec, skip_idle, opcodes=False,
                      output_file=None, compression='auto', diff_baseline=None):
    """Create the appropriate collector based on format type.

    Args:
        format_type: The output format ('pstats', 'collapsed', 'flamegraph', 'gecko', 'heatmap', 'binary', 'diff_flamegraph')
        sample_interval_usec: Sampling interval in microseconds
        skip_idle: Whether to skip idle samples
        opcodes: Whether to collect opcode information (only used by gecko format
                 for creating interval markers in Firefox Profiler)
        output_file: Output file path (required for binary format)
        compression: Compression type for binary format ('auto', 'zstd', 'none')
        diff_baseline: Path to baseline binary file for differential flamegraph

    Returns:
        A collector instance of the appropriate type
    """
    collector_class = COLLECTOR_MAP.get(format_type)
    if collector_class is None:
        raise ValueError(f"Unknown format: {format_type}")

    if format_type == "diff_flamegraph":
        if diff_baseline is None:
            raise ValueError("Differential flamegraph requires a baseline file")
        if not os.path.exists(diff_baseline):
            raise ValueError(f"Baseline file not found: {diff_baseline}")
        return collector_class(
            sample_interval_usec,
            baseline_binary_path=diff_baseline,
            skip_idle=skip_idle
        )

    # Binary format requires output file and compression
    if format_type == "binary":
        if output_file is None:
            raise ValueError("Binary format requires an output file")
        return collector_class(output_file, sample_interval_usec, skip_idle=skip_idle,
                              compression=compression)

    # Gecko format never skips idle (it needs both GIL and CPU data)
    # and is the only format that uses opcodes for interval markers
    if format_type == "gecko":
        skip_idle = False
        return collector_class(sample_interval_usec, skip_idle=skip_idle, opcodes=opcodes)

    return collector_class(sample_interval_usec, skip_idle=skip_idle)