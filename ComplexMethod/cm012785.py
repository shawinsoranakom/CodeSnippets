def triton_config(
    size_hints,
    x,
    y=None,
    z=None,
    num_stages=1,
    num_elements_per_warp=256,
    min_elem_per_thread=0,
    num_warps=None,
    matrix_instr=None,
    waves_per_eu=None,
    kpack=None,
) -> Config:
    """
    Construct a pointwise triton config with some adjustment heuristics
    based on size_hints. Size_hints is a tuple of numels in each tile
    dimension and will be rounded up to the nearest power of 2.

    num_elements_per_warp is a suggestion for controlling how many warps
    the triton config should contain. e.g.: if x=16, y=8, z=4 then
    num_elements = 16*8*4 = 512. Then if we set num_elements_per_warp=128,
    we'll launch 512 (elem) / 128 (elem/warp) = 4 warps. Note that it's
    just a suggestion, and sometimes other adjustment heuristics will
    override the num_elements_per_warp.

    min_elem_per_thread controls the minimum number of elements
    processed by each thread. It's always enforced.
    """
    # Ideally we want to read this from some device config

    maxGridSize = [2147483647, 65535, 65535]

    target = conditional_product(x, y, z)
    if conditional_product(*size_hints.values()) < target:
        target //= 8

    # shrink sizes to size hints
    x = min(x, size_hints["x"])
    if y:
        y = min(y, size_hints["y"])
    if z:
        z = min(z, size_hints["z"])

    # if we are below original block size, scale up where we can;
    # or if the calculated grid size is larger than the limit, we bump up the corresponding dimension
    while x < min(size_hints["x"], TRITON_MAX_BLOCK["X"]) and (
        x * maxGridSize[0] < size_hints["x"] or conditional_product(x, y, z) < target
    ):
        x *= 2
    while (
        y
        and y < min(size_hints["y"], TRITON_MAX_BLOCK["Y"])
        and (
            y * maxGridSize[1] < size_hints["y"]
            or conditional_product(x, y, z) < target
        )
    ):
        y *= 2
    while (
        z
        and z < min(size_hints["z"], TRITON_MAX_BLOCK["Z"])
        and (
            z * maxGridSize[2] < size_hints["z"]
            or conditional_product(x, y, z) < target
        )
    ):
        z *= 2

    # Calculate num_warps if they are not hard passed to config
    if num_warps is None:
        num_warps = _num_warps(
            conditional_product(x, y, z) // num_elements_per_warp, min_num_warps=1
        )
    # we are going to arrive at 2 warps only if bs was too small due to
    # numel being too small. However to workaround some ptx bugs we still
    # want at least 4 warps if there's enough elements per thread
    # given that this is a rare situation, don't expect this to affect perf
    # in general
    # see https://github.com/pytorch/pytorch/pull/97950
    if conditional_product(x, y, z) >= 128 and not torch.version.hip:
        num_warps = max(num_warps, 4)
    xnumel = size_hints["x"]
    ynumel = size_hints.get("y")
    znumel = size_hints.get("z")

    # Increase x to satisfy min_elem_per_thread requirements.
    block_size = max(
        conditional_product(x, y, z),
        min_elem_per_thread * _NUM_THREADS_PER_WARP * num_warps,
    )
    x *= math.ceil(block_size / conditional_product(x, y, z))

    x, _num_blocks = _check_max_grid_x(size_hints, x, num_warps)
    x = min(x, size_hints["x"])

    cfg = {"XBLOCK": x}
    if y:
        cfg["YBLOCK"] = y
    if z:
        cfg["ZBLOCK"] = z
    check_max_block(cfg)
    check_config(cfg, xnumel=xnumel, ynumel=ynumel, znumel=znumel)
    config = Config(cfg, num_warps=num_warps, num_stages=num_stages)

    if torch.version.hip:
        if matrix_instr is not None:
            config.kwargs["matrix_instr_nonkdim"] = matrix_instr
        if waves_per_eu is not None:
            config.kwargs["waves_per_eu"] = waves_per_eu
        if kpack is not None:
            config.kwargs["kpack"] = kpack

    return config