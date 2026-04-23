def marlin_moe_generate_valid_test_cases():
    import itertools

    def is_valid(
        a_type,
        b_type,
        c_type,
        group_blocks,
        m,
        n,
        k,
        e,
        topk,
        ep_size,
        act_order,
        is_k_full,
    ):
        group_size = group_blocks if group_blocks <= 0 else group_blocks * 16
        if group_size > 0 and k % group_size != 0:
            return False
        if act_order and group_size in [-1, k, n]:
            return False
        if group_size in [k, n]:
            return False
        if b_type == scalar_types.float8_e4m3fn and group_size == 32 and is_k_full:
            return False
        return a_type.size_bits < 16 or a_type is c_type

    cases = []
    for quant_test_config in MOE_MARLIN_QUANT_TEST_CONFIGS:
        f16_types = [scalar_types.float16]
        inner_combinations = list(
            itertools.product(
                quant_test_config.get("a_type", f16_types),
                [quant_test_config["b_type"]],
                quant_test_config.get("c_type", f16_types),
                quant_test_config["group_blocks"],
            )
        )

        supports_act_order = quant_test_config.get("support_act_order", False)

        for sub_case in inner_combinations:
            if (
                sub_case[0] == scalar_types.float8_e4m3fn
                and current_platform.get_device_capability() not in [89, 120]
            ):
                continue

            for scenario in MARLIN_MOE_SCENARIOS:
                m, n, k, e, topk, ep_size, act_order, is_k_full = scenario
                if act_order and not supports_act_order:
                    continue
                args = sub_case + (m, n, k, e, topk, ep_size, act_order, is_k_full)
                if is_valid(*args):
                    cases.append(args)
    return cases