def config_from_args(args) -> tuple[LaunchConfig, Callable | str, list[str]]:
    # If ``args`` not passed, defaults to ``sys.argv[:1]``
    min_nodes, max_nodes = parse_min_max_nnodes(args.nnodes)
    if not (0 < min_nodes <= max_nodes):
        raise AssertionError(
            f"min_nodes must be > 0 and <= max_nodes, got min_nodes={min_nodes}, max_nodes={max_nodes}"
        )
    if args.max_restarts < 0:
        raise AssertionError("max_restarts must be >= 0")

    if (
        hasattr(args, "master_addr")
        and args.rdzv_backend != "static"
        and not args.rdzv_endpoint
    ):
        logger.warning(
            "master_addr is only used for static rdzv_backend and when rdzv_endpoint "
            "is not specified."
        )

    nproc_per_node = determine_local_world_size(args.nproc_per_node)
    if "OMP_NUM_THREADS" not in os.environ and nproc_per_node > 1:
        omp_num_threads = 1
        logger.warning(
            "\n*****************************************\n"
            "Setting OMP_NUM_THREADS environment variable for each process to be "
            "%s in default, to avoid your system being overloaded, "
            "please further tune the variable for optimal performance in "
            "your application as needed. \n"
            "*****************************************",
            omp_num_threads,
        )
        # This env variable will be passed down to the subprocesses
        os.environ["OMP_NUM_THREADS"] = str(omp_num_threads)

    log_line_prefix_template = os.getenv("TORCHELASTIC_LOG_LINE_PREFIX_TEMPLATE")

    rdzv_configs = _parse_rendezvous_config(args.rdzv_conf)

    if args.rdzv_backend == "static":
        rdzv_configs["rank"] = args.node_rank

    rdzv_endpoint = get_rdzv_endpoint(args)

    ranks: set[int] | None = None
    if args.local_ranks_filter:
        try:
            ranks = set(map(int, args.local_ranks_filter.split(",")))
            if not ranks:
                raise AssertionError("ranks set cannot be empty")
        except Exception as e:
            raise ValueError(
                "--local_ranks_filter must be a comma-separated list of integers e.g. --local_ranks_filter=0,1,2"
            ) from e

    logs_specs_cls: type[LogsSpecs] = _get_logs_specs_class(args.logs_specs)

    logs_specs = logs_specs_cls(
        log_dir=args.log_dir,
        redirects=Std.from_str(args.redirects),
        tee=Std.from_str(args.tee),
        local_ranks_filter=ranks,
    )
    numa_options = (
        None
        if args.numa_binding is None
        else _NumaOptions(affinity_mode=_AffinityMode(args.numa_binding))
    )

    config = LaunchConfig(
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        nproc_per_node=nproc_per_node,
        run_id=args.rdzv_id,
        role=args.role,
        rdzv_endpoint=rdzv_endpoint,
        rdzv_backend=args.rdzv_backend,
        rdzv_configs=rdzv_configs,
        max_restarts=args.max_restarts,
        monitor_interval=args.monitor_interval,
        start_method=args.start_method,
        log_line_prefix_template=log_line_prefix_template,
        local_addr=args.local_addr,
        logs_specs=logs_specs,
        event_log_handler=args.event_log_handler,
        numa_options=numa_options,
        signals_to_handle=args.signals_to_handle,
        duplicate_stdout_filters=args.duplicate_stdout_filters,
        duplicate_stderr_filters=args.duplicate_stderr_filters,
        virtual_local_rank=args.virtual_local_rank,
        shutdown_timeout=args.shutdown_timeout,
    )

    with_python = not args.no_python
    cmd: Callable | str
    cmd_args = []
    use_env = get_use_env(args)
    if args.run_path:
        cmd = run_script_path
        cmd_args.append(args.training_script)
    else:
        if with_python:
            cmd = os.getenv("PYTHON_EXEC", sys.executable)
            cmd_args.append("-u")
            if args.module:
                cmd_args.append("-m")
            cmd_args.append(args.training_script)
        else:
            if args.module:
                raise ValueError(
                    "Don't use both the '--no-python' flag"
                    " and the '--module' flag at the same time."
                )
            cmd = args.training_script
    if not use_env:
        cmd_args.append(f"--local-rank={macros.local_rank}")
    cmd_args.extend(args.training_script_args)

    return config, cmd, cmd_args