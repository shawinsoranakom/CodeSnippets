def create_kernel_configs(args: argparse.Namespace, permute_x: bool, permute_y: bool):
    block_m_range = power_of_two_range(args.BLOCK_SIZE_M[0], args.BLOCK_SIZE_M[1])
    block_n_range = power_of_two_range(args.BLOCK_SIZE_N[0], args.BLOCK_SIZE_N[1])
    block_k_range = power_of_two_range(args.BLOCK_SIZE_K[0], args.BLOCK_SIZE_K[1])
    num_warps_range = multiples_of_range(args.num_warps[0], args.num_warps[1], step = 2)
    num_stages_range = multiples_of_range(
        args.num_stages[0], args.num_stages[1], step = 1
    )

    mode = args.mode
    kernel_configs = []
    for (
        block_m,
        block_n,
        block_k,
        num_warps,
        num_stages,
        tma_load_a,
        tma_load_b,
    ) in product(
        block_m_range,
        block_n_range,
        block_k_range,
        num_warps_range,
        num_stages_range,
        [True, False],
        [True, False],
    ):
        if mode == "forward":
            kernel_config = KernelConfigForward(
                BLOCK_SIZE_M = block_m,
                BLOCK_SIZE_N = block_n,
                BLOCK_SIZE_K = block_k,
                num_warps = num_warps,
                num_stages = num_stages,
                use_tma_load_w = tma_load_a,
                use_tma_load_x = tma_load_b,
                permute_x = permute_x,
                permute_y = permute_y,
            )
        elif mode == "dW":
            kernel_config = KernelConfigBackward_dW(
                BLOCK_SIZE_M = block_m,
                BLOCK_SIZE_N = block_n,
                BLOCK_SIZE_K = block_k,
                num_warps = num_warps,
                num_stages = num_stages,
                use_tma_load_dy = tma_load_a,
                use_tma_load_x = tma_load_b,
                permute_x = permute_x,
                permute_y = permute_y,
            )
        elif mode == "dX":
            kernel_config = KernelConfigBackward_dX(
                BLOCK_SIZE_M = block_m,
                BLOCK_SIZE_N = block_n,
                BLOCK_SIZE_K = block_k,
                num_warps = num_warps,
                num_stages = num_stages,
                use_tma_load_dy = tma_load_a,
                use_tma_load_w = tma_load_b,
                permute_x = permute_x,
                permute_y = permute_y,
            )
        else:
            raise ValueError(f"Invalid mode: {mode}")
        kernel_configs.append(kernel_config)

    logging.info(f"Pruning {len(kernel_configs)} kernel configs")

    pruned_configs = []
    for config in kernel_configs:
        if mode == "forward":
            if permute_x and config.use_tma_load_x:
                continue
        elif mode == "dW":
            if permute_x and config.use_tma_load_x:
                continue
            if permute_y and config.use_tma_load_dy:
                continue
        elif mode == "dX":
            if permute_y and config.use_tma_load_dy:
                continue
        pruned_configs.append(config)
    logging.info(f"After pruning, {len(pruned_configs)} kernel configs")

    return pruned_configs