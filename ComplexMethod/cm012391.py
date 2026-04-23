def early_config_prune(g, m, dtsize, configs, named_args):
    pruned_configs = []
    for config in configs:
        kw = config.kwargs
        BLOCK_M, BLOCK_N, BLOCK_K, num_stages, num_warps, num_consumer_groups = (
            kw["BLOCK_M"],
            kw["BLOCK_N"],
            kw["BLOCK_K"],
            config.num_stages,
            config.num_warps,
            getattr(config, "num_consumer_groups", 0),
        )

        # 1. Prune NV configs depending on g and m.
        if not has_free_symbols((g, m)):
            a_is_2d, b_is_2d = named_args["A_IS_2D"], named_args["B_IS_2D"]
            m_avg = m // g if a_is_2d and not b_is_2d else m
            if m_avg <= 16:
                if BLOCK_M > 32:
                    continue
            elif m_avg <= 32:
                if BLOCK_M > 64:
                    continue
            elif m_avg <= 64:
                if BLOCK_M <= 16:
                    continue
            else:
                if BLOCK_M <= 32:
                    continue

        # 2. make sure we have enough smem
        max_shared_memory = get_gpu_shared_memory()

        required_shared_memory = (BLOCK_M + BLOCK_N) * BLOCK_K * num_stages * dtsize
        if required_shared_memory > max_shared_memory:
            continue

        use_warp_specialization = num_consumer_groups >= 1

        # 3. make sure we can partition for ws
        if use_warp_specialization:
            if num_warps != 4:
                continue

            # "tritongpu-warp-spec-data-partition"
            m_slice = BLOCK_M // num_consumer_groups
            n_slice = BLOCK_N // num_consumer_groups
            if m_slice < 64 and n_slice < 256:
                continue

        pruned_configs.append(config)

    return pruned_configs