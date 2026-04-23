def main():
    parser = argparse.ArgumentParser(
        description="Universal vLLM attention benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Config file
    parser.add_argument(
        "--config",
        help="Path to YAML config file (overrides other args)",
    )

    # Backend selection
    parser.add_argument(
        "--backends",
        "--decode-backends",
        nargs="+",
        help="Decode backends to benchmark (flash, triton, flashinfer, cutlass_mla, "
        "flashinfer_mla, flashattn_mla, flashmla)",
    )
    parser.add_argument(
        "--backend",
        help="Single backend (alternative to --backends)",
    )
    parser.add_argument(
        "--prefill-backends",
        nargs="+",
        help="Prefill backends to compare (fa2, fa3, fa4). "
        "Uses the first decode backend for impl construction.",
    )

    # Batch specifications
    parser.add_argument(
        "--batch-specs",
        nargs="+",
        default=None,
        help="Batch specifications using extended grammar",
    )

    # Model config
    parser.add_argument("--num-layers", type=int, default=10, help="Number of layers")
    parser.add_argument("--head-dim", type=int, default=128, help="Head dimension")
    parser.add_argument("--num-q-heads", type=int, default=32, help="Query heads")
    parser.add_argument("--num-kv-heads", type=int, default=8, help="KV heads")
    parser.add_argument("--block-size", type=int, default=16, help="Block size")

    # Benchmark settings
    parser.add_argument("--device", default="cuda:0", help="Device")
    parser.add_argument("--repeats", type=int, default=1, help="Repetitions")
    parser.add_argument("--warmup-iters", type=int, default=3, help="Warmup iterations")
    parser.add_argument("--profile-memory", action="store_true", help="Profile memory")
    parser.add_argument(
        "--kv-cache-dtype",
        default="auto",
        choices=["auto", "fp8"],
        help="KV cache dtype: auto or fp8",
    )
    parser.add_argument(
        "--cuda-graphs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Launch kernels with CUDA graphs to eliminate CPU overhead"
            "in measurements (default: True)"
        ),
    )

    # Parameter sweep (use YAML config for advanced sweeps)
    parser.add_argument(
        "--sweep-param",
        help="Parameter name to sweep (e.g., num_kv_splits, reorder_batch_threshold)",
    )
    parser.add_argument(
        "--sweep-values",
        type=int,
        nargs="+",
        help="Values to sweep for the parameter",
    )

    # Output
    parser.add_argument("--output-csv", help="Save to CSV")
    parser.add_argument("--output-json", help="Save to JSON")

    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]vLLM Attention Benchmark[/]")

    # Load config from YAML if provided
    if args.config:
        console.print(f"[yellow]Loading config from: {args.config}[/]")
        yaml_config = load_config_from_yaml(args.config)

        # Show description if available
        if "description" in yaml_config:
            console.print(f"[dim]{yaml_config['description']}[/]")

        # Override args with YAML values, but CLI args take precedence
        # Check if CLI provided backends (they would be non-None and not default)
        cli_backends_provided = args.backend is not None or args.backends is not None

        # Backend(s) - only use YAML if CLI didn't specify
        if not cli_backends_provided:
            if "backend" in yaml_config:
                args.backend = yaml_config["backend"]
                args.backends = None
            elif "backends" in yaml_config:
                args.backends = yaml_config["backends"]
                args.backend = None
            elif "decode_backends" in yaml_config:
                args.backends = yaml_config["decode_backends"]
                args.backend = None

        # Prefill backends (e.g., ["fa3", "fa4"])
        args.prefill_backends = yaml_config.get("prefill_backends", None)

        # Check for special modes
        args.mode = yaml_config.get("mode", None)

        # Batch specs and sizes
        # Support both explicit batch_specs and generated batch_spec_ranges
        # CLI --batch-specs takes precedence over YAML when provided.
        cli_batch_specs_provided = args.batch_specs is not None
        if not cli_batch_specs_provided:
            if "batch_spec_ranges" in yaml_config:
                # Generate batch specs from ranges
                generated_specs = generate_batch_specs_from_ranges(
                    yaml_config["batch_spec_ranges"]
                )
                # Combine with any explicit batch_specs
                if "batch_specs" in yaml_config:
                    args.batch_specs = yaml_config["batch_specs"] + generated_specs
                else:
                    args.batch_specs = generated_specs
                console.print(
                    f"[dim]Generated {len(generated_specs)} batch specs from ranges[/]"
                )
            elif "batch_specs" in yaml_config:
                args.batch_specs = yaml_config["batch_specs"]

        args.batch_sizes = yaml_config.get("batch_sizes", None)

        # Model config
        if "model" in yaml_config:
            model = yaml_config["model"]
            args.num_layers = model.get("num_layers", args.num_layers)
            args.head_dim = model.get("head_dim", args.head_dim)
            args.num_q_heads = model.get("num_q_heads", args.num_q_heads)
            args.num_kv_heads = model.get("num_kv_heads", args.num_kv_heads)
            args.block_size = model.get("block_size", args.block_size)

        # Benchmark settings (top-level keys)
        if "device" in yaml_config:
            args.device = yaml_config["device"]
        if "repeats" in yaml_config:
            args.repeats = yaml_config["repeats"]
        if "warmup_iters" in yaml_config:
            args.warmup_iters = yaml_config["warmup_iters"]
        if "profile_memory" in yaml_config:
            args.profile_memory = yaml_config["profile_memory"]
        if "kv_cache_dtype" in yaml_config:
            args.kv_cache_dtype = yaml_config["kv_cache_dtype"]
        if "cuda_graphs" in yaml_config:
            args.cuda_graphs = yaml_config["cuda_graphs"]

        # Parameter sweep configuration
        if "parameter_sweep" in yaml_config:
            sweep_config = yaml_config["parameter_sweep"]
            args.parameter_sweep = ParameterSweep(
                param_name=sweep_config["param_name"],
                values=sweep_config["values"],
                include_auto=sweep_config.get("include_auto", False),
                label_format=sweep_config.get(
                    "label_format", "{backend}_{param_name}_{value}"
                ),
            )
        else:
            args.parameter_sweep = None

        # Model parameter sweep configuration
        if "model_parameter_sweep" in yaml_config:
            sweep_config = yaml_config["model_parameter_sweep"]
            args.model_parameter_sweep = ModelParameterSweep(
                param_name=sweep_config["param_name"],
                values=sweep_config["values"],
                label_format=sweep_config.get(
                    "label_format", "{backend}_{param_name}_{value}"
                ),
            )
        else:
            args.model_parameter_sweep = None

        # Output
        if "output" in yaml_config:
            output = yaml_config["output"]
            if "csv" in output and not args.output_csv:
                args.output_csv = output["csv"]
            if "json" in output and not args.output_json:
                args.output_json = output["json"]

        console.print()

    # Handle CLI-based parameter sweep (if not from YAML)
    if (
        (not hasattr(args, "parameter_sweep") or args.parameter_sweep is None)
        and args.sweep_param
        and args.sweep_values
    ):
        args.parameter_sweep = ParameterSweep(
            param_name=args.sweep_param,
            values=args.sweep_values,
            include_auto=False,
            label_format="{backend}_{param_name}_{value}",
        )

    # Determine backends
    backends = args.backends or ([args.backend] if args.backend else ["flash"])
    prefill_backends = getattr(args, "prefill_backends", None)
    if not args.batch_specs:
        args.batch_specs = ["q2k", "8q1s1k"]
    console.print(f"Backends: {', '.join(backends)}")
    if prefill_backends:
        console.print(f"Prefill backends: {', '.join(prefill_backends)}")
    console.print(f"Batch specs: {', '.join(args.batch_specs)}")
    console.print(f"KV cache dtype: {args.kv_cache_dtype}")
    console.print(f"CUDA graphs: {args.cuda_graphs}")
    console.print()

    init_workspace_manager(args.device)

    # Run benchmarks
    all_results = []

    # Handle special mode: decode_vs_prefill comparison
    if hasattr(args, "mode") and args.mode == "decode_vs_prefill":
        console.print("[yellow]Mode: Decode vs Prefill pipeline comparison[/]")
        console.print(
            "[dim]For each query length, testing both decode and prefill pipelines[/]"
        )
        console.print("[dim]Using batched execution for optimal performance[/]")

        # Extract batch sizes from config
        batch_sizes = getattr(args, "batch_sizes", [1])
        backend = backends[0]  # Use first backend (should only be one)

        # Calculate total benchmarks
        total = len(batch_sizes)

        with tqdm(total=total, desc="Benchmarking") as pbar:
            for batch_size in batch_sizes:
                # Prepare all configs for this batch size
                configs_with_thresholds = []

                for spec in args.batch_specs:
                    # Parse the batch spec to get query length
                    requests = parse_batch_spec(spec)
                    if not requests:
                        console.print(
                            f"[red]Error: Could not parse batch spec '{spec}'[/]"
                        )
                        continue

                    # Get query length from first request
                    query_length = requests[0].q_len

                    # Create batch spec for this batch size
                    # For batch_size > 1, we need to prepend the count
                    batch_spec = f"{batch_size}{spec}" if batch_size > 1 else spec

                    # Create base config (without backend name)
                    base_config = BenchmarkConfig(
                        backend=backend,  # Will be overridden later
                        batch_spec=batch_spec,
                        num_layers=args.num_layers,
                        head_dim=args.head_dim,
                        num_q_heads=args.num_q_heads,
                        num_kv_heads=args.num_kv_heads,
                        block_size=args.block_size,
                        device=args.device,
                        repeats=args.repeats,
                        warmup_iters=args.warmup_iters,
                        profile_memory=args.profile_memory,
                        kv_cache_dtype=args.kv_cache_dtype,
                        use_cuda_graphs=args.cuda_graphs,
                    )

                    # Add decode pipeline config
                    decode_threshold = query_length
                    config_decode = replace(
                        base_config,
                        backend=f"{backend}_decode_qlen{query_length}_bs{batch_size}",
                    )
                    configs_with_thresholds.append((config_decode, decode_threshold))

                    # Add prefill pipeline config if query_length > 1
                    if query_length > 1:
                        prefill_threshold = query_length - 1
                        config_prefill = replace(
                            base_config,
                            backend=f"{backend}_prefill_qlen{query_length}"
                            f"_bs{batch_size}",
                        )
                        configs_with_thresholds.append(
                            (config_prefill, prefill_threshold)
                        )

                # Run all benchmarks for this batch size in one go (batched mode)
                try:
                    from mla_runner import run_mla_benchmark as run_mla

                    # Use batched API: pass list of (config, threshold) tuples
                    timing_results = run_mla(backend, configs_with_thresholds)

                    # Create BenchmarkResult objects from timing results
                    for (config, _), timing in zip(
                        configs_with_thresholds, timing_results
                    ):
                        result = BenchmarkResult(
                            config=config,
                            mean_time=timing["mean"],
                            std_time=timing["std"],
                            min_time=timing["min"],
                            max_time=timing["max"],
                            throughput_tokens_per_sec=timing.get("throughput", None),
                        )
                        all_results.append(result)

                except Exception as e:
                    import traceback

                    console.print(
                        f"[red]Error running batched benchmarks for "
                        f"batch_size={batch_size}: {e}[/]"
                    )
                    console.print("[red]Traceback:[/]")
                    traceback.print_exc()
                    # Add error results for all configs
                    for config, _ in configs_with_thresholds:
                        result = BenchmarkResult(
                            config=config,
                            mean_time=float("inf"),
                            std_time=0,
                            min_time=float("inf"),
                            max_time=float("inf"),
                            error=str(e),
                        )
                        all_results.append(result)

                pbar.update(1)

        # Display decode vs prefill results
        console.print("\n[bold green]Decode vs Prefill Results:[/]")

        # Group by batch size
        by_batch_size = {}
        for r in all_results:
            if r.success:
                # Extract batch size from backend name
                parts = r.config.backend.split("_")
                bs_part = [p for p in parts if p.startswith("bs")]
                if bs_part:
                    bs = int(bs_part[0][2:])
                    if bs not in by_batch_size:
                        by_batch_size[bs] = []
                    by_batch_size[bs].append(r)

        # For each batch size, analyze crossover point
        for bs in sorted(by_batch_size.keys()):
            console.print(f"\n[bold cyan]Batch size: {bs}[/]")
            results = by_batch_size[bs]

            # Group by query length
            by_qlen = {}
            for r in results:
                parts = r.config.backend.split("_")
                qlen_part = [p for p in parts if p.startswith("qlen")]
                if qlen_part:
                    qlen = int(qlen_part[0][4:])
                    if qlen not in by_qlen:
                        by_qlen[qlen] = {}

                    pipeline = "decode" if "decode" in r.config.backend else "prefill"
                    by_qlen[qlen][pipeline] = r

            # Find crossover point
            last_decode_faster = None
            for qlen in sorted(by_qlen.keys()):
                pipelines = by_qlen[qlen]
                if "decode" in pipelines and "prefill" in pipelines:
                    decode_time = pipelines["decode"].mean_time
                    prefill_time = pipelines["prefill"].mean_time
                    faster = "decode" if decode_time < prefill_time else "prefill"

                    speedup = (
                        prefill_time / decode_time
                        if decode_time < prefill_time
                        else decode_time / prefill_time
                    )

                    console.print(
                        f"  qlen={qlen:3d}: decode={decode_time:.6f}s, "
                        f"prefill={prefill_time:.6f}s -> "
                        f"[bold]{faster}[/] ({speedup:.2f}x)"
                    )

                    if faster == "decode":
                        last_decode_faster = qlen

            if last_decode_faster is not None:
                optimal_threshold = last_decode_faster
                console.print(
                    f"\n  [bold green]Optimal threshold for batch_size={bs}: "
                    f"{optimal_threshold}[/]"
                )
                console.print(
                    f"  [dim](Use decode pipeline for query_length <= "
                    f"{optimal_threshold})[/]"
                )
            else:
                console.print(
                    f"\n  [yellow]Prefill always faster for batch_size={bs}[/]"
                )

    # Handle model parameter sweep mode
    elif hasattr(args, "model_parameter_sweep") and args.model_parameter_sweep:
        # Model parameter sweep
        base_config_args = {
            "num_layers": args.num_layers,
            "head_dim": args.head_dim,
            "num_q_heads": args.num_q_heads,
            "num_kv_heads": args.num_kv_heads,
            "block_size": args.block_size,
            "device": args.device,
            "repeats": args.repeats,
            "warmup_iters": args.warmup_iters,
            "profile_memory": args.profile_memory,
            "kv_cache_dtype": args.kv_cache_dtype,
            "use_cuda_graphs": args.cuda_graphs,
        }
        all_results = run_model_parameter_sweep(
            backends,
            args.batch_specs,
            base_config_args,
            args.model_parameter_sweep,
            console,
        )

    # Handle parameter sweep mode (unified)
    elif hasattr(args, "parameter_sweep") and args.parameter_sweep:
        # Unified parameter sweep
        base_config_args = {
            "num_layers": args.num_layers,
            "head_dim": args.head_dim,
            "num_q_heads": args.num_q_heads,
            "num_kv_heads": args.num_kv_heads,
            "block_size": args.block_size,
            "device": args.device,
            "repeats": args.repeats,
            "warmup_iters": args.warmup_iters,
            "profile_memory": args.profile_memory,
            "kv_cache_dtype": args.kv_cache_dtype,
            "use_cuda_graphs": args.cuda_graphs,
        }
        all_results = run_parameter_sweep(
            backends, args.batch_specs, base_config_args, args.parameter_sweep, console
        )

    else:
        # Normal mode: compare backends
        decode_results = []
        prefill_results = []

        # Run decode backend comparison
        if not prefill_backends:
            # No prefill backends specified: compare decode backends as before
            total = len(backends) * len(args.batch_specs)

            with tqdm(total=total, desc="Benchmarking") as pbar:
                for spec in args.batch_specs:
                    for backend in backends:
                        config = BenchmarkConfig(
                            backend=backend,
                            batch_spec=spec,
                            num_layers=args.num_layers,
                            head_dim=args.head_dim,
                            num_q_heads=args.num_q_heads,
                            num_kv_heads=args.num_kv_heads,
                            block_size=args.block_size,
                            device=args.device,
                            repeats=args.repeats,
                            warmup_iters=args.warmup_iters,
                            profile_memory=args.profile_memory,
                            kv_cache_dtype=args.kv_cache_dtype,
                            use_cuda_graphs=args.cuda_graphs,
                        )

                        result = run_benchmark(config)
                        decode_results.append(result)

                        if not result.success:
                            console.print(
                                f"[red]Error {backend} {spec}: {result.error}[/]"
                            )

                        pbar.update(1)

            console.print("\n[bold green]Results:[/]")
            formatter = ResultsFormatter(console)
            formatter.print_table(decode_results, backends)

        # Run prefill backend comparison
        if prefill_backends:
            # Use first decode backend for impl construction
            decode_backend = backends[0]
            total = len(prefill_backends) * len(args.batch_specs)

            console.print(
                f"[yellow]Prefill comparison mode: "
                f"using {decode_backend} for decode impl[/]"
            )

            with tqdm(total=total, desc="Prefill benchmarking") as pbar:
                for spec in args.batch_specs:
                    for pb in prefill_backends:
                        config = BenchmarkConfig(
                            backend=decode_backend,
                            batch_spec=spec,
                            num_layers=args.num_layers,
                            head_dim=args.head_dim,
                            num_q_heads=args.num_q_heads,
                            num_kv_heads=args.num_kv_heads,
                            block_size=args.block_size,
                            device=args.device,
                            repeats=args.repeats,
                            warmup_iters=args.warmup_iters,
                            profile_memory=args.profile_memory,
                            prefill_backend=pb,
                        )

                        result = run_benchmark(config)

                        # Label result with prefill backend name for display
                        labeled_config = replace(result.config, backend=pb)
                        result = replace(result, config=labeled_config)
                        prefill_results.append(result)

                        if not result.success:
                            console.print(f"[red]Error {pb} {spec}: {result.error}[/]")

                        pbar.update(1)

            console.print("\n[bold green]Prefill Backend Results:[/]")
            formatter = ResultsFormatter(console)
            formatter.print_table(
                prefill_results, prefill_backends, compare_to_fastest=True
            )

        all_results = decode_results + prefill_results

    # Save results
    if all_results:
        formatter = ResultsFormatter(console)
        if args.output_csv:
            formatter.save_csv(all_results, args.output_csv)
        if args.output_json:
            formatter.save_json(all_results, args.output_json)