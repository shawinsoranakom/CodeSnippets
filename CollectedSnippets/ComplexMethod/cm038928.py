def main(args):
    # Initialize workspace manager (required for CUTLASS MoE kernels)
    device = torch.device("cuda:0")
    init_workspace_manager(device)

    print("Benchmarking models:")
    for i, model in enumerate(args.models):
        print(f"[{i}]  {model}")

    all_results = []

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

                for per_act_token in args.per_act_token_opts:
                    for per_out_ch in args.per_out_ch_opts:
                        print(
                            f"\n=== {model}, experts={num_experts}, topk={topk},"
                            f"per_act={per_act_token}, per_out_ch={per_out_ch} ==="
                        )

                        config_results = []
                        for size_m in args.batch_sizes:
                            mkn = (size_m, size_k, size_n)
                            result = bench_run(
                                [],  # Not used anymore
                                model,
                                num_experts,
                                topk,
                                per_act_token,
                                per_out_ch,
                                mkn,
                            )
                            if result:
                                config_results.append(result)

                        # Print results table for this configuration
                        if config_results:
                            print(
                                f"\n{'Batch Size':<12}"
                                f"{'Triton (us)':<15}"
                                f"{'CUTLASS (us)':<15}"
                            )
                            print("-" * 45)
                            for result in config_results:
                                print(
                                    f"{result['batch_size']:<12}"
                                    f"{result['triton_time_us']:<15.2f}"
                                    f"{result['cutlass_time_us']:<15.2f}"
                                )

                            all_results.extend(config_results)

    print(f"\nTotal benchmarks completed: {len(all_results)}")