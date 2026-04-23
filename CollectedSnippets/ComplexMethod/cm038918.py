def main():
    parser = FlexibleArgumentParser(description="Benchmark device communicators")

    parser.add_argument(
        "--sequence-lengths",
        type=int,
        nargs="+",
        default=DEFAULT_SEQUENCE_LENGTHS,
        help="Sequence lengths to benchmark (tensor shape: seq_len x hidden_size)",
    )

    parser.add_argument(
        "--num-warmup", type=int, default=5, help="Number of warmup iterations"
    )

    parser.add_argument(
        "--num-trials", type=int, default=50, help="Number of benchmark trials"
    )

    parser.add_argument("--output-json", type=str, help="Output results to JSON file")

    args = parser.parse_args()

    # Initialize distributed
    if not dist.is_initialized():
        dist.init_process_group(backend="gloo")
    rank = dist.get_rank()
    world_size = dist.get_world_size()

    # Set device
    device = torch.device(f"cuda:{rank}")
    torch.accelerator.set_device_index(device)

    # Get CPU process group
    cpu_group = dist.new_group(backend="gloo")

    # Disable USE_SYMM_MEM to avoid affecting the max_sizes
    # in symm_mem and custom_all_reduce for benchmark
    os.environ["VLLM_ALLREDUCE_USE_SYMM_MEM"] = "0"

    # Initialize benchmark
    benchmark = CommunicatorBenchmark(
        rank, world_size, device, cpu_group, args.sequence_lengths
    )

    # Run benchmarks
    all_results = {}

    for seq_len in args.sequence_lengths:
        if rank == 0:
            logger.info(
                "Benchmarking sequence length: %s (tensor shape: %s x %s)",
                seq_len,
                seq_len,
                HIDDEN_SIZE,
            )

        results = benchmark.benchmark_allreduce(
            sequence_length=seq_len,
            num_warmup=args.num_warmup,
            num_trials=args.num_trials,
        )

        all_results[seq_len] = results

        # Synchronize between ranks
        dist.barrier()

    # Print results (only rank 0)
    if rank == 0:
        print_results(all_results, args.sequence_lengths, world_size)

        # Save to JSON if requested
        if args.output_json:
            # Add speedup information to results
            enhanced_results = {}
            for seq_len, comm_results in all_results.items():
                enhanced_results[seq_len] = {
                    "timings": comm_results,
                    "speedup_info": _calculate_speedup_info(comm_results),
                }

            output_data = {
                "world_size": world_size,
                "dtype": str(BENCHMARK_DTYPE),
                "hidden_size": HIDDEN_SIZE,
                "sequence_lengths": args.sequence_lengths,
                "num_warmup": args.num_warmup,
                "num_trials": args.num_trials,
                "cuda_graph_capture_cycles": CUDA_GRAPH_CAPTURE_CYCLES,
                "results": enhanced_results,
            }

            with open(args.output_json, "w") as f:
                json.dump(output_data, f, indent=2)

            logger.info("Results saved to %s", args.output_json)

    # Cleanup
    if cpu_group != dist.group.WORLD:
        dist.destroy_process_group(cpu_group)