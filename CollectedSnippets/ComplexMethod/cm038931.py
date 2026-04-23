def main():
    parser = argparse.ArgumentParser(
        description="Benchmark fused collective operations"
    )
    parser.add_argument(
        "--num-tokens",
        type=int,
        nargs="+",
        default=[128, 512, 1024, 2048],
        help="Numbers of tokens to test",
    )
    parser.add_argument(
        "--hidden-dim", type=int, default=8192, help="Hidden dimension size"
    )
    parser.add_argument(
        "--dtypes",
        type=str,
        nargs="+",
        default=["bfloat16"],
        choices=["float16", "bfloat16", "float32"],
        help="Data types to test",
    )
    parser.add_argument(
        "--no-residual",
        action="store_true",
        help="Skip residual connection tests",
    )

    parser.add_argument(
        "--quant-modes",
        type=str,
        default="none,fp8,fp4",
        help=(
            "Comma-separated quantization modes to run: none, fp8, fp4. "
            "Default: none,fp8,fp4"
        ),
    )

    parser.add_argument(
        "--warmup", type=int, default=5, help="Number of warmup iterations"
    )
    parser.add_argument(
        "--trials", type=int, default=20, help="Number of benchmark trials"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="""Output file path for markdown results 
                (default: benchmark_results_<timestamp>.md)
        """,
    )

    parser.add_argument(
        "--no-oneshot",
        action="store_true",
        help="Skip oneshot benchmarks",
    )

    args = parser.parse_args()

    # Check if running with torchrun (required for collective operations)
    if "RANK" not in os.environ or "WORLD_SIZE" not in os.environ:
        raise RuntimeError(
            "Must run with torchrun for distributed benchmarking. "
            "Example: torchrun --nproc_per_node=2 benchmark_fused_collective.py"
        )

    # Initialize distributed environment
    rank = int(os.environ["RANK"])
    world_size = int(os.environ["WORLD_SIZE"])

    device = torch.device(f"cuda:{rank}")
    torch.accelerator.set_device_index(device)
    torch.set_default_device(device)

    init_distributed_environment()
    initialize_model_parallel(tensor_model_parallel_size=world_size)

    # Validate world size (must be > 1 for collective operations)
    if world_size <= 1:
        raise ValueError(
            "World size must be > 1 for collective operations benchmarking. "
            f"Current world size: {world_size}. Use torchrun with --nproc_per_node > 1."
        )

    # Parse quantization modes
    valid_quant_modes = {"none", "fp8", "fp4"}
    raw_modes = [
        m.strip().lower() for m in (args.quant_modes or "").split(",") if m.strip()
    ]
    quant_modes = set(raw_modes) if raw_modes else {"none", "fp8", "fp4"}
    invalid = sorted(list(quant_modes - valid_quant_modes))
    if invalid:
        raise ValueError(
            f"Invalid --quant-modes entries: {','.join(invalid)}. "
            f"Valid options are: {','.join(sorted(valid_quant_modes))}."
        )

    if rank == 0:
        logger.info("Running benchmark with world_size=%s, rank=%s", world_size, rank)
        logger.info("Quantization modes: %s", ",".join(sorted(list(quant_modes))))
        if flashinfer_comm is not None:
            logger.info(
                "FlashInfer available - will benchmark fused operations",
            )
        else:
            logger.info(
                "FlashInfer not available - only benchmarking standard operations"
            )

    # Convert dtype strings to torch dtypes
    dtype_map = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    dtypes = [dtype_map[dt] for dt in args.dtypes]

    # Test configurations
    residual_options = [True] if not args.no_residual else [False]

    configs = list(itertools.product(args.num_tokens, dtypes, residual_options))

    # Setup FlashInfer workspaces for all backends
    allreduce_params = None

    if flashinfer_comm is not None:
        # Use the largest hidden dimension for workspace setup
        max_element_size = max(torch.finfo(dt).bits // 8 for dt in dtypes)
        workspace_dtype = (
            torch.float32
            if max_element_size == 4
            else (torch.bfloat16 if torch.bfloat16 in dtypes else torch.float16)
        )
        max_num_token = _FI_MAX_SIZES.get(world_size) // (
            args.hidden_dim * max_element_size
        )

        for backend in FLASHINFER_BACKENDS:
            setup_flashinfer_workspace(
                backend=backend,
                world_size=world_size,
                rank=rank,
                hidden_dim=args.hidden_dim,
                max_token_num=max_num_token,
                dtype=workspace_dtype,
            )

        if _FI_WORKSPACES:
            allreduce_params = FlashInferFusedAllReduceParams(
                max_token_num=max_num_token,
            )

    # Collect all results for markdown export
    all_results = []

    try:
        # Run benchmarks
        for num_tokens, dtype, use_residual in configs:
            if rank == 0:
                logger.info(
                    "\nTesting:  num_tokens=%s, hidden_dim=%s, dtype=%s, residual=%s",
                    num_tokens,
                    args.hidden_dim,
                    dtype,
                    use_residual,
                )

            results = run_benchmarks(
                num_tokens,
                args.hidden_dim,
                dtype,
                use_residual,
                allreduce_params,
                workspaces=_FI_WORKSPACES,
                quant_modes=quant_modes,
                no_oneshot=args.no_oneshot,
            )

            # Store results for markdown export
            if rank == 0:
                # Calculate input size in MB
                input_size_mb = (
                    num_tokens * args.hidden_dim * torch.finfo(dtype).bits
                ) / (8 * 1024 * 1024)
                all_results.append(
                    {
                        "num_tokens": num_tokens,
                        "hidden_dim": args.hidden_dim,
                        "dtype": str(dtype).replace("torch.", ""),
                        "use_residual": use_residual,
                        "quant_modes": sorted(list(quant_modes)),
                        "input_size_mb": input_size_mb,
                        "results": results,
                    }
                )

                print_results(
                    results,
                    num_tokens,
                    args.hidden_dim,
                    dtype,
                    use_residual,
                    quant_modes,
                    input_size_mb,
                )

        # Save results to markdown file
        if args.output_file and rank == 0:
            save_results_to_file(all_results, world_size, args, rank)

    finally:
        # Cleanup
        cleanup_flashinfer_workspaces()

        dist.barrier()