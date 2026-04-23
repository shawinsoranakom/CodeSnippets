def _discover_aten_op(
    opinfos: list[opinfo_core.OpInfo],
    device: str,
    dtype: torch.dtype,
) -> OpOverload | None:
    """Discover the aten op dispatched by the first valid sample."""
    for opinfo in opinfos:
        try:
            samples = list(opinfo.sample_inputs(device, dtype))
        except Exception:
            continue
        for sample in samples:
            tensors = extract_tensors_from_sample(sample)
            if not tensors or any(0 in t.shape for _, t in tensors):
                continue
            capture = get_aten_op_for_sample(opinfo.op, sample, opinfo.name)
            aten_op = capture.best_match
            if aten_op is not None:
                return aten_op
    return None