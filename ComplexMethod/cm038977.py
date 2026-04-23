def run_parameter_sweep(
    backends: list[str],
    batch_specs: list[str],
    base_config_args: dict,
    sweep: ParameterSweep,
    console: Console,
) -> list[BenchmarkResult]:
    """
    Run parameter sweep for given backends and batch specs.

    Args:
        backends: List of backend names
        batch_specs: List of batch specifications
        base_config_args: Base configuration arguments (num_layers, head_dim, etc.)
        sweep: ParameterSweep configuration
        console: Rich console for output

    Returns:
        List of BenchmarkResult objects
    """
    all_results = []

    # Build list of values to sweep (including auto if requested)
    sweep_values = list(sweep.values)
    if sweep.include_auto:
        sweep_values.append("auto")

    console.print(f"[yellow]Sweep mode: testing {sweep.param_name} = {sweep_values}[/]")

    total = len(backends) * len(batch_specs) * len(sweep_values)

    with tqdm(total=total, desc="Benchmarking") as pbar:
        for backend in backends:
            for spec in batch_specs:
                for value in sweep_values:
                    # Create config with original backend for running
                    config = BenchmarkConfig(
                        backend=backend, batch_spec=spec, **base_config_args
                    )

                    # Prepare kwargs for benchmark runner
                    kwargs = {}
                    if value != "auto":
                        kwargs[sweep.param_name] = value

                    # Run benchmark
                    result = run_benchmark(config, **kwargs)

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

    # Display sweep results
    console.print("\n[bold green]Sweep Results:[/]")
    backend_labels = [sweep.get_label(b, v) for b in backends for v in sweep_values]
    formatter = ResultsFormatter(console)
    formatter.print_table(all_results, backend_labels)

    # Show optimal values
    console.print(f"\n[bold cyan]Optimal {sweep.param_name} per batch spec:[/]")
    by_spec = {}
    for r in all_results:
        if r.success:
            spec = r.config.batch_spec
            if spec not in by_spec:
                by_spec[spec] = []
            by_spec[spec].append(r)

    for spec in sorted(by_spec.keys(), key=batch_spec_sort_key):
        results = by_spec[spec]
        best = min(results, key=lambda r: r.mean_time)
        console.print(
            f"  {spec}: [bold green]{best.config.backend}[/] ({best.mean_time:.6f}s)"
        )

    return all_results