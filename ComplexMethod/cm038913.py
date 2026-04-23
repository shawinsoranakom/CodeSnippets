def main(args):
    print("Benchmarking models:")
    for i, model in enumerate(args.models):
        print(f"[{i}]  {model}")
    results: list[benchmark.Measurement] = []

    for model in args.models:
        for layer in WEIGHT_SHAPES[model]:
            size_k = layer[0]
            size_n = layer[1]

            if len(args.limit_k) > 0 and size_k not in args.limit_k:
                continue

            if len(args.limit_n) > 0 and size_n not in args.limit_n:
                continue

            for act_order in ACT_ORDER_OPTS:
                if (
                    len(args.limit_act_order) > 0
                    and act_order not in args.limit_act_order
                ):
                    continue

                for is_k_full in K_FULL_OPTS:
                    if (
                        len(args.limit_k_full) > 0
                        and is_k_full not in args.limit_k_full
                    ):
                        continue

                    for quant_type in query_marlin_supported_quant_types():
                        if (
                            len(args.limit_num_bits) > 0
                            and quant_type.size_bits not in args.limit_num_bits
                        ):
                            continue

                        for group_size in (
                            MARLIN_SUPPORTED_GROUP_SIZES
                            + FP4_MARLIN_SUPPORTED_GROUP_SIZES
                        ):
                            if (
                                len(args.limit_group_size) > 0
                                and group_size not in args.limit_group_size
                            ):
                                continue

                            # For act_order, the group_size must be less than
                            # size_k
                            if act_order and (group_size == size_k or group_size == -1):
                                continue

                            for size_m in args.batch_sizes:
                                bench_run(
                                    results,
                                    model,
                                    act_order,
                                    is_k_full,
                                    quant_type,
                                    group_size,
                                    size_m,
                                    size_k,
                                    size_n,
                                )

    compare = benchmark.Compare(results)
    compare.print()