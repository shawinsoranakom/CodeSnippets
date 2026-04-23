def is_mm_compute_bound(M: int, K: int, N: int, dtype: torch.dtype) -> bool:
    denominator = M * K + N * K + M * N
    if denominator == 0:
        return False
    arithmetic_intensity = (M * N * K) / denominator

    # we have experienced some large perf hits in this case, even in bandwidth bound regimes
    if (
        dtype is torch.bfloat16
        and K > M
        and K > N
        and (torch.xpu.is_available() or torch.cuda.get_device_capability() < (9, 0))
    ):  # doesn't repro on h100s:
        return True

    # Fails with AMD
    try:
        machine_balance = (
            1000 * utils.get_device_tflops(dtype)
        ) / utils.get_gpu_dram_gbps()
    except Exception:
        return True

    # dram_gbps might be underestimating bandwidth because of cache.
    # if we estimate machine balance too low we might miss some speedups,
    # if we estimate too high there will be unnecessary compilation time increase.
    # TODO - finetune coefficient here. As a reference point, Triton mm model assumes
    # 80% of reads are in cache and cache is 4x faster than dram_gbps
    machine_balance = machine_balance * 0.5

    return arithmetic_intensity > machine_balance