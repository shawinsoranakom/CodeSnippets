def triton_config_tiled_reduction(
    size_hints, x, y, r, num_stages=1, register_intensive=False, waves_per_eu=None
):
    """
    Construct a tile reduction triton config with some adjustment
    heuristics based on size_hints. Size_hints is a tuple of numels in
    each tile dimension and will be rounded up to the nearest power of 2.
    """
    # Convert the linear reduction numel into a multi-dimensional block.
    rnumels = _get_nd_reduction_numels(r, size_hints)

    # shrink sizes to size hints
    x = min(x, size_hints["x"])
    y = min(y, size_hints["y"])

    def total_numel() -> int:
        return conditional_product(x, y, *rnumels.values())

    target = total_numel()
    if conditional_product(*size_hints.values()) < target:
        target //= 8

    # if we are below original block size, scale up where we can
    while x < size_hints["x"] and total_numel() < target:
        x *= 2
    for prefix in sorted(rnumels):
        while rnumels[prefix] < size_hints[prefix] and total_numel() < target:
            rnumels[prefix] *= 2
    while y < size_hints["y"] and total_numel() < target:
        y *= 2

    cfg = _get_config({"x": x, "y": y, **rnumels})
    num_warps = _num_warps(total_numel() // 256, min_num_warps=1)
    num_warps = _num_warps(
        num_warps, max_num_warps=16, register_intensive=register_intensive
    )
    check_config(cfg, xnumel=size_hints["x"], ynumel=size_hints["y"])
    check_max_block(cfg)
    config = Config(cfg, num_warps=num_warps, num_stages=num_stages)
    if torch.version.hip:
        if waves_per_eu is not None:
            config.kwargs["waves_per_eu"] = waves_per_eu
    return config