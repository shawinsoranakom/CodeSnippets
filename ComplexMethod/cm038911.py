def main(args):
    # Initialize workspace manager (required for CUTLASS MoE kernels)
    device = torch.device("cuda:0")
    init_workspace_manager(device)

    print("Benchmarking models:")
    for i, model in enumerate(args.models):
        print(f"[{i}]  {model}")

    results: list[benchmark.Measurement] = []

    for model in args.models:
        for tp in args.tp_sizes:
            for layer in WEIGHT_SHAPES_MOE[model]:
                num_experts = layer[0]
                topk = layer[1]
                size_k = layer[2]
                size_n = layer[3] // tp

                if len(args.limit_k) > 0 and size_k not in args.limit_k:
                    continue

                if len(args.limit_n) > 0 and size_n not in args.limit_n:
                    continue

                for per_act_token in PER_ACT_TOKEN_OPTS:
                    for per_out_ch in PER_OUT_CH_OPTS:
                        for size_m in args.batch_sizes:
                            mkn = (size_m, size_k, size_n)
                            bench_run(
                                results,
                                model,
                                num_experts,
                                topk,
                                per_act_token,
                                per_out_ch,
                                mkn,
                            )

    compare = benchmark.Compare(results)
    compare.print()