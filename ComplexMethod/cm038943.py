def get_configs_compute_bound(use_fp16, block_quant_shape) -> list[dict[str, int]]:
    configs: list[BenchmarkConfig] = []

    if current_platform.is_rocm():
        param_ranges = get_rocm_tuning_space(use_fp16)
    else:
        # Reduced search space for faster tuning.
        # TODO(woosuk): Increase the search space and use a performance model to
        # prune the search space.
        block_m_range = [16, 32, 64, 128, 256]
        block_n_range = [32, 64, 128, 256]
        block_k_range = [64, 128, 256]
        num_warps_range = [4, 8]
        group_m_range = [1, 16, 32, 64]
        num_stage_range = [2, 3, 4, 5]

        param_ranges = {
            "BLOCK_SIZE_M": block_m_range,
            "BLOCK_SIZE_N": block_n_range,
            "BLOCK_SIZE_K": block_k_range,
            "GROUP_SIZE_M": group_m_range,
            "num_warps": num_warps_range,
            "num_stages": num_stage_range,
        }

    keys, values = zip(*param_ranges.items())
    for config_values in product(*values):
        config = dict(zip(keys, config_values))
        configs.append(config)

    # Remove configs that are not compatible with fp8 block quantization
    # BLOCK_SIZE_K must be a multiple of block_k
    # BLOCK_SIZE_N must be a multiple of block_n
    if block_quant_shape is not None and not use_fp16:
        block_n, block_k = block_quant_shape[0], block_quant_shape[1]
        for config in configs[:]:
            if (
                config["BLOCK_SIZE_K"] % block_k != 0
                or config["BLOCK_SIZE_N"] % block_n != 0
            ):
                configs.remove(config)
    return configs