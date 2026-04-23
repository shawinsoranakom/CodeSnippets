def explore_comb_workloads(
    server: ServerProcess | None,
    bench_cmd: list[str],
    *,
    serve_comb: ParameterSweepItem,
    bench_comb: ParameterSweepItem,
    link_vars: list[tuple[str, str]],
    workload_var: WorkloadVariable,
    workload_iters: int,
    experiment_dir: Path,
    num_runs: int,
    dry_run: bool,
):
    print("[WL START]")
    print(f"Serve parameters: {serve_comb.as_text() or '(None)'}")
    print(f"Bench parameters: {bench_comb.as_text() or '(None)'}")
    print(f"Number of workload iterations: {workload_iters}")

    if workload_iters < 2:
        raise ValueError("`workload_iters` should be at least 2")

    dataset_size = DEFAULT_NUM_PROMPTS
    if "num_prompts" in bench_comb:
        dataset_size = int(bench_comb["num_prompts"])  # type: ignore
    else:
        for i, arg in enumerate(bench_cmd):
            if arg == "--num-prompts" and i + 1 < len(bench_cmd):
                dataset_size = int(bench_cmd[i + 1])
                break
            elif arg.startswith("--num-prompts="):
                dataset_size = int(arg.split("=", 1)[1])
                break

    print(f"Dataset size: {dataset_size}")

    serial_workload_data = run_comb_workload(
        server,
        bench_cmd,
        serve_comb=serve_comb,
        bench_comb=bench_comb | {"max_concurrency": 1},
        link_vars=link_vars,
        experiment_dir=experiment_dir,
        num_runs=num_runs,
        dry_run=dry_run,
        workload_var=workload_var,
        workload_value=1,
    )
    batch_workload_data = run_comb_workload(
        server,
        bench_cmd,
        serve_comb=serve_comb,
        bench_comb=bench_comb | {"max_concurrency": dataset_size},
        link_vars=link_vars,
        experiment_dir=experiment_dir,
        num_runs=num_runs,
        dry_run=dry_run,
        workload_var=workload_var,
        workload_value=dataset_size,
    )

    if serial_workload_data is None or batch_workload_data is None:
        if dry_run:
            print("Omitting intermediate Workload iterations.")
            print("[WL END]")

        return

    serial_workload_value = math.ceil(
        _estimate_workload_avg(serial_workload_data, workload_var)
    )
    print(f"Serial inference: {workload_var}={serial_workload_value}")

    batch_workload_value = math.floor(
        _estimate_workload_avg(batch_workload_data, workload_var)
    )
    print(f"Batch inference: {workload_var}={batch_workload_value}")

    # Avoid duplicated runs for intermediate values if the range between
    # `serial_workload_value` and `batch_workload_value` is small
    inter_workload_values = np.linspace(
        serial_workload_value, batch_workload_value, workload_iters
    )[1:-1]
    inter_workload_values = sorted(set(map(round, inter_workload_values)))

    inter_workloads_data: list[dict[str, object]] = []
    for inter_workload_value in inter_workload_values:
        print(f"Exploring: {workload_var}={inter_workload_value}")
        inter_workload_data = run_comb_workload(
            server,
            bench_cmd,
            serve_comb=serve_comb,
            bench_comb=bench_comb,
            link_vars=link_vars,
            experiment_dir=experiment_dir,
            num_runs=num_runs,
            dry_run=dry_run,
            workload_var=workload_var,
            workload_value=inter_workload_value,
        )
        if inter_workload_data is not None:
            inter_workloads_data.extend(inter_workload_data)

    print("[WL END]")

    return serial_workload_data + inter_workloads_data + batch_workload_data