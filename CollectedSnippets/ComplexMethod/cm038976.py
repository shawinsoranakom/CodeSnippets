def run_model_parameter_sweep(
    backends: list[str],
    batch_specs: list[str],
    base_config_args: dict,
    sweep: ModelParameterSweep,
    console: Console,
) -> list[BenchmarkResult]:
    """
    Run model parameter sweep for given backends and batch specs.

    Args:
        backends: List of backend names
        batch_specs: List of batch specifications
        base_config_args: Base configuration arguments (num_layers, head_dim, etc.)
        sweep: ModelParameterSweep configuration
        console: Rich console for output

    Returns:
        List of BenchmarkResult objects
    """
    all_results = []

    console.print(
        f"[yellow]Model sweep mode: testing {sweep.param_name} = {sweep.values}[/]"
    )

    total = len(backends) * len(batch_specs) * len(sweep.values)

    with tqdm(total=total, desc="Benchmarking") as pbar:
        for backend in backends:
            for spec in batch_specs:
                for value in sweep.values:
                    # Create config with modified model parameter
                    config_args = base_config_args.copy()
                    config_args[sweep.param_name] = value

                    # Create config with original backend for running
                    clean_config = BenchmarkConfig(
                        backend=backend, batch_spec=spec, **config_args
                    )

                    # Run benchmark
                    result = run_benchmark(clean_config)

                    # Replace backend with labeled version for display
                    backend_label = sweep.get_label(backend, value)
                    labeled_config = replace(result.config, backend=backend_label)
                    result = replace(result, config=labeled_config)
                    all_results.append(result)

                    if not result.success:
                        console.print(
                            f"[red]Error {backend} {spec} {sweep.param_name}="
                            f"{value}: {result.error}[/]"
                        )

                    pbar.update(1)

    # Display sweep results - create separate table for each parameter value
    console.print("\n[bold green]Model Parameter Sweep Results:[/]")
    formatter = ResultsFormatter(console)

    # Group results by parameter value and extract backend mapping
    by_param_value = {}
    backend_mapping = {}  # Maps labeled backend -> original backend

    for r in all_results:
        # Extract original backend and param value from labeled backend
        # The label format is: {backend}_{param_name}_{value}
        # We need to reverse engineer this
        labeled_backend = r.config.backend

        # Try each backend to find which one this result belongs to
        for backend in backends:
            for value in sweep.values:
                expected_label = sweep.get_label(backend, value)
                if labeled_backend == expected_label:
                    backend_mapping[labeled_backend] = backend
                    param_value = str(value)

                    if param_value not in by_param_value:
                        by_param_value[param_value] = []
                    by_param_value[param_value].append(r)
                    break

    # Create a table for each parameter value
    sorted_param_values = sorted(
        by_param_value.keys(), key=lambda x: int(x) if x.isdigit() else x
    )

    for param_value in sorted_param_values:
        console.print(f"\n[bold cyan]{sweep.param_name} = {param_value}[/]")
        param_results = by_param_value[param_value]

        # Create modified results with original backend names
        modified_results = []
        for r in param_results:
            # Get the original backend name from our mapping
            original_backend = backend_mapping[r.config.backend]
            modified_config = replace(r.config, backend=original_backend)
            modified_result = replace(r, config=modified_config)
            modified_results.append(modified_result)

        # Print table with original backend names
        formatter.print_table(modified_results, backends, compare_to_fastest=True)

    # Show optimal backend for each (param_value, batch_spec) combination
    console.print(
        f"\n[bold cyan]Optimal backend for each ({sweep.param_name}, batch_spec):[/]"
    )

    # Group by (param_value, batch_spec)
    by_param_and_spec = {}
    for r in all_results:
        if r.success:
            # Find which (backend, value) this result corresponds to
            labeled_backend = r.config.backend
            for backend in backends:
                for value in sweep.values:
                    expected_label = sweep.get_label(backend, value)
                    if labeled_backend == expected_label:
                        param_value = str(value)
                        spec = r.config.batch_spec
                        key = (param_value, spec)

                        if key not in by_param_and_spec:
                            by_param_and_spec[key] = []
                        by_param_and_spec[key].append(r)
                        break

    # Sort by param value then spec (batch_size, q_len, kv_len)
    sorted_keys = sorted(
        by_param_and_spec.keys(),
        key=lambda x: (
            int(x[0]) if x[0].isdigit() else x[0],
            batch_spec_sort_key(x[1]),
        ),
    )

    current_param_value = None
    for param_value, spec in sorted_keys:
        # Print header when param value changes
        if param_value != current_param_value:
            console.print(f"\n  [bold]{sweep.param_name}={param_value}:[/]")
            current_param_value = param_value

        results = by_param_and_spec[(param_value, spec)]
        best = min(results, key=lambda r: r.mean_time)

        # Extract original backend name using the mapping
        backend_name = backend_mapping[best.config.backend]

        # Show all backends' times for comparison
        times_str = " | ".join(
            [
                f"{backend_mapping[r.config.backend]}: {r.mean_time:.6f}s"
                for r in sorted(results, key=lambda r: r.mean_time)
            ]
        )

        console.print(
            f"    {spec:12s} -> [bold green]{backend_name:15s}[/] ({times_str})"
        )

    return all_results