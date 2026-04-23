def _format_sample_repro(sample: SampleInput, aten_op: OpOverload | None = None) -> str:
    """Format a SampleInput's values for repro output, using schema arg names."""
    # Get argument names from the aten op schema if available.
    # Schema args are ordered: the first is the input, then positional args,
    # then keyword-only args (which appear in sample.kwargs).
    arg_names: list[str] = []
    if aten_op is not None:
        try:
            arg_names = [a.name for a in aten_op._schema.arguments]
        except Exception:
            pass

    parts = []
    # input is the first positional arg
    name = arg_names[0] if arg_names else "input"
    parts.append(f"{name}={sample.input!r}")
    # remaining positional args
    for i, arg in enumerate(sample.args):
        name = arg_names[1 + i] if 1 + i < len(arg_names) else f"args[{i}]"
        parts.append(f"{name}={arg!r}")
    # kwargs — use their actual key names (already named)
    for k, v in sample.kwargs.items():
        parts.append(f"{k}={v!r}")
    return ", ".join(parts)