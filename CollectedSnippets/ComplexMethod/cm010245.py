def scatter_mm_meta(
    M,
    K,
    N,
    Ms,
    Ks,
    GROUP_SIZE=None,
    TILE_M=None,
    TILE_N=None,
    SPLIT_N=None,
    num_warps=None,
    num_stages=None,
    **extra,
):
    if {TILE_M, TILE_N, SPLIT_N, num_warps, num_stages, GROUP_SIZE} == {None}:
        device_name = _get_device_name()
        meta = get_meta(
            "scatter_mm",
            (M, K, N, Ms, Ks),
            device_name,
            version=(0, torch.float16, 0.5),
        )
        if meta is not None:
            meta.update(**extra)
            return meta
        # The following parameters are optimized for the performance
        # equilibrium points of bsr-dense and dense-dense matrix
        # multiplications when using GPU card NVIDIA GeForce RTX 2060
        # SUPER. For points far from the performance equilibrium
        # points as well as for other GPU cards, the optimal
        # parameters are likely different from what specified below.
        if (M, K, N) == (256,) * 3:
            if (Ms, Ks) == (16, 16):
                SPLIT_N = 1
                TILE_M = 16
                TILE_N = 16
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (32, 32):
                SPLIT_N = 2
                TILE_M = 32
                TILE_N = 16
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (64, 64):
                SPLIT_N = 1
                TILE_M = 32
                TILE_N = 32
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (128, 128):
                SPLIT_N = 1
                TILE_M = 32
                TILE_N = 32
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
        elif (M, K, N) == (512,) * 3:
            if (Ms, Ks) == (16, 16):
                SPLIT_N = 8
                TILE_M = 16
                TILE_N = 64
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 2  # noqa: E225, E231
            elif (Ms, Ks) == (32, 32):
                SPLIT_N = 8
                TILE_M = 32
                TILE_N = 64
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 2  # noqa: E225, E231
            elif (Ms, Ks) == (64, 64):
                SPLIT_N = 4
                TILE_M = 32
                TILE_N = 128
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (128, 128):
                SPLIT_N = 8
                TILE_M = 64
                TILE_N = 64
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
        elif (M, K, N) == (1024,) * 3:
            if (Ms, Ks) == (16, 16):
                SPLIT_N = 4
                TILE_M = 16
                TILE_N = 128
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 1  # noqa: E225, E231
            elif (Ms, Ks) == (32, 32):
                SPLIT_N = 8
                TILE_M = 32
                TILE_N = 64
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 1  # noqa: E225, E231
            elif (Ms, Ks) == (64, 64):
                SPLIT_N = 16
                TILE_M = 64
                TILE_N = 64
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 2  # noqa: E225, E231
            elif (Ms, Ks) == (128, 128):
                SPLIT_N = 16
                TILE_M = 64
                TILE_N = 64
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (256, 256):
                SPLIT_N = 16
                TILE_M = 64
                TILE_N = 64
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
        elif (M, K, N) == (2048,) * 3:
            if (Ms, Ks) == (16, 16):
                SPLIT_N = 4
                TILE_M = 16
                TILE_N = 128
                GROUP_SIZE = 8
                num_stages = 1
                num_warps = 1  # noqa: E225, E231
            elif (Ms, Ks) == (32, 32):
                SPLIT_N = 4
                TILE_M = 32
                TILE_N = 64
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 1  # noqa: E225, E231
            elif (Ms, Ks) == (64, 64):
                SPLIT_N = 4
                TILE_M = 64
                TILE_N = 128
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (128, 128):
                SPLIT_N = 8
                TILE_M = 64
                TILE_N = 64
                GROUP_SIZE = 4
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
            elif (Ms, Ks) == (256, 256):
                SPLIT_N = 4
                TILE_M = 64
                TILE_N = 64
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 4  # noqa: E225, E231
        elif (M, K, N) == (4096,) * 3:
            if (Ms, Ks) == (16, 16):
                SPLIT_N = 2
                TILE_M = 16
                TILE_N = 256
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 2  # noqa: E225, E231
            elif (Ms, Ks) == (32, 32):
                SPLIT_N = 2
                TILE_M = 32
                TILE_N = 64
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 1  # noqa: E225, E231
            elif (Ms, Ks) == (64, 64):
                SPLIT_N = 2
                TILE_M = 64
                TILE_N = 128
                GROUP_SIZE = 2
                num_stages = 1
                num_warps = 4  # noqa: E225, E231

    if SPLIT_N is None:
        # Assume NVIDIA GeForce RTX 2060 SUPER:
        # With the probality of 92% (99.9% when N > 512), the
        # performance will not be worse more than 2% from the
        # performance when using an optimal value.  Otherwise, when N
        # <= 512, using the following heuristics may give upto 15%
        # lower performance.
        SPLIT_N = {
            16: 1,
            32: 2,
            64: 4,
            128: 8,
            256: 16,
            512: 8,
            1024: 16,
            4096: 32,
            8192: 64,
        }.get(N, 16)
        if Ms >= 512 and N >= 2048:
            SPLIT_N = 1
    Ns = N // SPLIT_N
    if TILE_M is None:
        TILE_M = min(64 if Ns < 512 else 32, Ms)
    if TILE_N is None:
        TILE_N = min(64 if Ns < 512 else 32, Ns)
    num_stages = num_stages or 1
    if num_warps is None:
        if min(M, N) > 1024:
            num_warps = {16: 1, 32: 1, 64: 2}.get(Ms, 4)
        elif min(M, N) == 1024:
            num_warps = {16: 1, 32: 1, 64: 2}.get(Ms, 4)
        elif min(M, N) == 256:
            num_warps = {16: 1, 32: 4}.get(Ms, 4)
        else:
            num_warps = {16: 1, 32: 2}.get(Ms, 4)
    GROUP_SIZE = GROUP_SIZE or 4

    if TILE_M > Ms:
        raise AssertionError(f"TILE_M ({TILE_M}) must be <= Ms ({Ms})")
    if TILE_N > Ns:
        raise AssertionError(f"TILE_N ({TILE_N}) must be <= Ns ({Ns})")
    if Ms > M:
        raise AssertionError(f"Ms ({Ms}) must be <= M ({M})")
    if Ns > N:
        raise AssertionError(f"Ns ({Ns}) must be <= N ({N})")
    if Ks > K:
        raise AssertionError(f"Ks ({Ks}) must be <= K ({K})")

    return dict(
        TILE_M=TILE_M,
        TILE_N=TILE_N,
        GROUP_SIZE=GROUP_SIZE,
        num_stages=num_stages,
        num_warps=num_warps,
        SPLIT_N=SPLIT_N,
        **extra,
    )