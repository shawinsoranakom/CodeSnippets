def run(args: argparse.Namespace, bench_ctxs: list[BenchmarkContext]):
    if args.cuda_graph_nops is not None:
        assert args.cuda_graph_nops > 0
        print(f"Benchmarking {args.cuda_graph_nops} invocations inside a CUDA Graph")
    else:
        print(f"CUDA Graphs not enabled.\n{use_cuda_graph_recommendation()}")

    timers = []
    for bench_ctx in bench_ctxs:
        for seq_len in args.seq_lengths:
            bench_ops: list[OpType] = args.op_types
            seq_len_timers = []
            for bench_op in bench_ops:
                for num_slices in bench_op.num_slices():
                    _ctx = bench_ctx.with_seq_length(seq_len).with_num_slices(
                        num_slices
                    )
                    # Benchmark torch.mm as a roofline
                    seq_len_timers.append(
                        bench_torch_mm(
                            _ctx, args.arg_pool_size, bench_op, args.cuda_graph_nops
                        )
                    )

                    # Benchmark bench_op
                    expand_fn_add_inputs = (
                        [None]
                        if bench_op.is_shrink_fn() or bench_op.is_fused_moe_lora_fn()
                        else args.expand_fn_add_inputs
                    )
                    for add_input_arg in expand_fn_add_inputs:
                        seq_len_timers.append(
                            bench_optype(
                                _ctx,
                                args.arg_pool_size,
                                bench_op,
                                args.cuda_graph_nops,
                                add_input_arg,
                                args.test_correctness,
                            )
                        )

            print_timers(seq_len_timers)
            timers.extend(seq_len_timers)

    # Result stdout dump
    print("== All Results ====")
    print_timers(timers, args)

    if args.output_directory:
        # Result file dump
        od = Path(args.output_directory)
        if not od.exists():
            od.mkdir()

        timestamp = int(time.time())
        pkl_file = od / f"lora_bench-{timestamp}.pkl"
        print(f"Writing benchmarks to {pkl_file}")
        with open(pkl_file, "wb") as f:
            pickle.dump(timers, f)