def run(
    strategies: str,
    models: Optional[str],
    categories: Optional[str],
    skip_categories: Optional[str],
    tests: Optional[str],
    attempts: int,
    parallel: int,
    timeout: int,
    cutoff: Optional[int],
    no_cutoff: bool,
    max_steps: int,
    maintain: bool,
    improve: bool,
    explore: bool,
    no_dep: bool,
    workspace: Optional[Path],
    challenges_dir: Optional[Path],
    reports_dir: Optional[Path],
    keep_answers: bool,
    quiet: bool,
    verbose: bool,
    json_output: bool,
    ci_mode: bool,
    fresh: bool,
    retry_failures: bool,
    reset_strategies: tuple[str, ...],
    reset_models: tuple[str, ...],
    reset_challenges: tuple[str, ...],
    debug: bool,
    external_benchmark: Optional[str],
    benchmark_split: str,
    benchmark_subset: Optional[str],
    benchmark_limit: Optional[int],
    benchmark_cache_dir: Optional[Path],
):
    """Run benchmarks with specified configurations."""
    # Handle timeout/cutoff options
    if cutoff is not None:
        timeout = cutoff
    if no_cutoff:
        timeout = 0  # 0 means no timeout
    # Parse strategies
    strategy_list = [s.strip() for s in strategies.split(",")]
    invalid_strategies = [s for s in strategy_list if s not in STRATEGIES]
    if invalid_strategies:
        console.print(f"[red]Invalid strategies: {invalid_strategies}[/red]")
        console.print(f"Available: {STRATEGIES}")
        sys.exit(1)

    # Parse models (auto-detect from API keys if not specified)
    if models is None:
        models = get_default_model()
        console.print(f"[dim]Auto-detected model: {models}[/dim]")

    model_list = [m.strip() for m in models.split(",")]
    invalid_models = [m for m in model_list if m not in MODEL_PRESETS]
    if invalid_models:
        console.print(f"[red]Invalid model presets: {invalid_models}[/red]")
        console.print(f"Available: {list(MODEL_PRESETS.keys())}")
        sys.exit(1)

    # Find challenges directory (not required for external benchmarks)
    if challenges_dir is None and not external_benchmark:
        challenges_dir = find_challenges_dir()
        if challenges_dir is None:
            console.print(
                "[red]Could not find challenges directory. "
                "Please specify with --challenges-dir or use --benchmark[/red]"
            )
            sys.exit(1)
    elif challenges_dir is None:
        # External benchmark - use a placeholder path
        challenges_dir = Path(".")

    # Set up paths
    if workspace is None:
        workspace = Path.cwd() / ".benchmark_workspaces"

    if reports_dir is None:
        reports_dir = Path.cwd() / "reports"

    # Build configurations
    configs: list[BenchmarkConfig] = []
    for strategy in strategy_list:
        for model_name in model_list:
            model = MODEL_PRESETS[model_name]
            configs.append(
                BenchmarkConfig(
                    strategy=cast(StrategyName, strategy),
                    model=model,
                    max_steps=max_steps,
                    timeout_seconds=timeout,
                )
            )

    # Create harness config
    harness_config = HarnessConfig(
        workspace_root=workspace,
        challenges_dir=challenges_dir,
        reports_dir=reports_dir,
        categories=categories.split(",") if categories else None,
        skip_categories=skip_categories.split(",") if skip_categories else None,
        test_names=tests.split(",") if tests else None,
        max_parallel=parallel,
        configs=configs,
        attempts=attempts,
        no_cutoff=no_cutoff,
        no_dep=no_dep,
        maintain=maintain,
        improve=improve,
        explore=explore,
        keep_answers=keep_answers,
        debug=debug,
        fresh=fresh,
        retry_failures=retry_failures,
        reset_strategies=list(reset_strategies) if reset_strategies else None,
        reset_models=list(reset_models) if reset_models else None,
        reset_challenges=list(reset_challenges) if reset_challenges else None,
        external_benchmark=external_benchmark,
        benchmark_split=benchmark_split,
        benchmark_subset=benchmark_subset,
        benchmark_limit=benchmark_limit,
        benchmark_cache_dir=benchmark_cache_dir,
    )

    # Determine UI mode
    # Auto-detect CI: CI env var set or not a TTY
    is_ci = ci_mode or os.environ.get("CI") == "true" or not sys.stdout.isatty()

    if json_output:
        ui_mode = "json"
    elif quiet:
        ui_mode = "quiet"
    elif is_ci:
        ui_mode = "ci"
    else:
        ui_mode = "default"

    # Print config summary (unless JSON mode)
    if ui_mode != "json":
        console.print()
        console.print("[bold]Direct Benchmark Harness[/bold]")
        console.print("=" * 50)
        console.print(f"Strategies: {strategy_list}")
        console.print(f"Models: {model_list}")
        console.print(f"Parallel: {parallel}")
        if external_benchmark:
            console.print(f"Benchmark: [cyan]{external_benchmark}[/cyan]")
            console.print(f"  Split: {benchmark_split}")
            if benchmark_subset:
                console.print(f"  Subset: {benchmark_subset}")
            if benchmark_limit:
                console.print(f"  Limit: {benchmark_limit}")
        else:
            console.print(f"Challenges: {challenges_dir}")
        if categories:
            console.print(f"Categories: {categories}")
        if skip_categories:
            console.print(f"Skip Categories: {skip_categories}")
        if tests:
            console.print(f"Tests: {tests}")
        if attempts > 1:
            console.print(f"Attempts: {attempts}")
        if no_cutoff:
            console.print("Cutoff: [yellow]disabled[/yellow]")
        elif timeout != 300:
            console.print(f"Timeout: {timeout}s")
        if maintain:
            console.print("Mode: [cyan]maintain[/cyan] (regression tests only)")
        if improve:
            console.print("Mode: [cyan]improve[/cyan] (non-regression tests only)")
        if explore:
            console.print("Mode: [cyan]explore[/cyan] (never-beaten only)")
        if no_dep:
            console.print("Dependencies: [yellow]ignored[/yellow]")
        if keep_answers:
            console.print("Keep answers: [green]yes[/green]")
        if debug:
            console.print("Debug: [yellow]enabled[/yellow]")
        if ui_mode == "ci":
            console.print("UI Mode: [cyan]ci[/cyan] (no live display)")
        console.print("=" * 50)
        console.print()

    # Run harness
    harness = BenchmarkHarness(harness_config)
    results = harness.run_sync(ui_mode=ui_mode, verbose=verbose, debug=debug)

    # Exit with appropriate code
    if not results:
        sys.exit(1)

    total_passed = sum(sum(1 for r in res if r.success) for res in results.values())
    total_run = sum(len(res) for res in results.values())

    if total_passed == 0:
        sys.exit(1)
    elif total_passed < total_run:
        sys.exit(0)  # Some passed
    else:
        sys.exit(0)