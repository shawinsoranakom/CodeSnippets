def run_multi_api_server(args: argparse.Namespace):
    assert not args.headless
    num_api_servers: int = args.api_server_count
    assert num_api_servers > 0

    if num_api_servers > 1:
        setup_multiprocess_prometheus()

    shutdown_requested = False

    # Catch SIGTERM and SIGINT to allow graceful shutdown.
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        logger.debug("Received %d signal.", signum)
        if not shutdown_requested:
            shutdown_requested = True
            raise SystemExit

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    listen_address, sock = setup_server(args)

    engine_args = vllm.AsyncEngineArgs.from_cli_args(args)
    engine_args._api_process_count = num_api_servers
    engine_args._api_process_rank = -1

    usage_context = UsageContext.OPENAI_API_SERVER
    vllm_config = engine_args.create_engine_config(usage_context=usage_context)

    if num_api_servers > 1 and envs.VLLM_ALLOW_RUNTIME_LORA_UPDATING:
        raise ValueError(
            "VLLM_ALLOW_RUNTIME_LORA_UPDATING cannot be used with api_server_count > 1"
        )

    executor_class = Executor.get_class(vllm_config)
    log_stats = not engine_args.disable_log_stats

    parallel_config = vllm_config.parallel_config
    dp_rank = parallel_config.data_parallel_rank
    assert parallel_config.local_engines_only or dp_rank == 0

    api_server_manager: APIServerProcessManager | None = None

    from vllm.v1.engine.utils import get_engine_zmq_addresses

    addresses = get_engine_zmq_addresses(vllm_config, num_api_servers)

    with launch_core_engines(
        vllm_config, executor_class, log_stats, addresses, num_api_servers
    ) as (local_engine_manager, coordinator, addresses, tensor_queue):
        # Construct common args for the APIServerProcessManager up-front.
        stats_update_address = None
        if coordinator:
            stats_update_address = coordinator.get_stats_publish_address()

        # Start API servers.
        api_server_manager = APIServerProcessManager(
            listen_address=listen_address,
            sock=sock,
            args=args,
            num_servers=num_api_servers,
            input_addresses=addresses.inputs,
            output_addresses=addresses.outputs,
            stats_update_address=stats_update_address,
            tensor_queue=tensor_queue,
        )

    # Wait for API servers.
    try:
        wait_for_completion_or_failure(
            api_server_manager=api_server_manager,
            engine_manager=local_engine_manager,
            coordinator=coordinator,
        )
    finally:
        timeout = shutdown_by = None
        if shutdown_requested:
            timeout = vllm_config.shutdown_timeout
            shutdown_by = time.monotonic() + timeout
            logger.info("Waiting up to %d seconds for processes to exit", timeout)

        def to_timeout(deadline: float | None) -> float | None:
            return (
                deadline if deadline is None else max(deadline - time.monotonic(), 0.0)
            )

        api_server_manager.shutdown(timeout=timeout)
        if local_engine_manager:
            local_engine_manager.shutdown(timeout=to_timeout(shutdown_by))
        if coordinator:
            coordinator.shutdown(timeout=to_timeout(shutdown_by))