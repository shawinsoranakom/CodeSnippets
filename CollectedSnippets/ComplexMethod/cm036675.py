def marlin_generate_valid_test_cases():
    all_combinations = itertools.product(
        DENSE_MARLIN_QUANT_TEST_CONFIGS,
        MNK_FACTORS,
        MARLIN_N_CHUNKS,
        MARLIN_K_CHUNKS,
        ACT_ORDER_OPTS,
        K_FULL_OPTS,
        USE_ATOMIC_ADD_OPTS,
        USE_FP32_REDUCE_OPTS,
    )

    def is_invalid(
        a_type,
        b_type,
        c_type,
        group_blocks,
        size_m,
        size_n,
        size_k,
        act_order,
        is_k_full,
        use_atomic_add,
        use_fp32_reduce,
    ):
        if use_atomic_add:
            if use_fp32_reduce:
                return False
            if (
                c_type == scalar_types.bfloat16
                and torch.cuda.get_device_capability()[0] < 9
            ):
                return False

        group_size = group_blocks if group_blocks <= 0 else group_blocks * 16
        if group_size > 0 and size_k % group_size != 0:
            return False

        if act_order and group_size in [-1, size_k]:
            return False
        if group_size == size_k:
            return False
        if not act_order and is_k_full:
            return False

        return a_type.size_bits < 16 or a_type is c_type

    cases = []
    for case in all_combinations:
        quant_test_config, mnk_factors, n_chunk, k_chunk, act_order, *_ = case
        size_m = mnk_factors[0]
        size_n = mnk_factors[1] * n_chunk
        size_k = mnk_factors[2] * k_chunk

        if act_order and not quant_test_config.get("support_act_order", False):
            continue

        f16_types = [scalar_types.float16, scalar_types.bfloat16]
        inner_combinations = itertools.product(
            quant_test_config.get("a_type", f16_types),
            [quant_test_config["b_type"]],
            quant_test_config.get("c_type", f16_types),
            quant_test_config["group_blocks"],
        )

        for sub_case in inner_combinations:
            if (
                sub_case[0] == scalar_types.float8_e4m3fn
                and current_platform.get_device_capability() not in [89, 120]
            ):
                continue
            args = sub_case + (size_m, size_n, size_k) + case[4:]
            if is_invalid(*args):
                cases.append(args)
    return cases