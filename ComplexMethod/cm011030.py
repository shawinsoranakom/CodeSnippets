def launch_agent(
    config: LaunchConfig,
    entrypoint: Callable | str | None,
    args: list[Any],
    health_check_server: HealthCheckServer | None = None,
) -> dict[int, Any]:
    if not config.run_id:
        run_id = str(uuid.uuid4().int)
        logger.warning("config has no run_id, generated a random run_id: %s", run_id)
        config.run_id = run_id

    entrypoint_name = _get_entrypoint_name(entrypoint, args)

    logger.info(
        "Starting elastic_operator with launch configs:\n"
        "  entrypoint               : %(entrypoint)s\n"
        "  min_nodes                : %(min_nodes)s\n"
        "  max_nodes                : %(max_nodes)s\n"
        "  nproc_per_node           : %(nproc_per_node)s\n"
        "  run_id                   : %(run_id)s\n"
        "  rdzv_backend             : %(rdzv_backend)s\n"
        "  rdzv_endpoint            : %(rdzv_endpoint)s\n"
        "  rdzv_configs             : %(rdzv_configs)s\n"
        "  max_restarts             : %(max_restarts)s\n"
        "  monitor_interval         : %(monitor_interval)s\n"
        "  log_dir                  : %(log_dir)s\n"
        "  metrics_cfg              : %(metrics_cfg)s\n"
        "  event_log_handler        : %(event_log_handler)s\n"
        "  numa_options             : %(numa_options)s\n"
        "  signals_to_handle        : %(signals_to_handle)s\n"
        "  duplicate_stdout_filters : %(duplicate_stdout_filters)s\n"
        "  duplicate_stderr_filters : %(duplicate_stderr_filters)s\n",
        {
            "entrypoint": entrypoint_name,
            "min_nodes": config.min_nodes,
            "max_nodes": config.max_nodes,
            "nproc_per_node": config.nproc_per_node,
            "run_id": config.run_id,
            "rdzv_backend": config.rdzv_backend,
            "rdzv_endpoint": config.rdzv_endpoint,
            "rdzv_configs": config.rdzv_configs,
            "max_restarts": config.max_restarts,
            "monitor_interval": config.monitor_interval,
            "log_dir": config.logs_specs.root_log_dir,  # type: ignore[union-attr]
            "metrics_cfg": config.metrics_cfg,
            "event_log_handler": config.event_log_handler,
            "numa_options": config.numa_options,
            "signals_to_handle": config.signals_to_handle,
            "duplicate_stdout_filters": config.duplicate_stdout_filters,
            "duplicate_stderr_filters": config.duplicate_stderr_filters,
        },
    )

    rdzv_parameters = RendezvousParameters(
        backend=config.rdzv_backend,
        endpoint=config.rdzv_endpoint,
        run_id=config.run_id,
        min_nodes=config.min_nodes,
        max_nodes=config.max_nodes,
        local_addr=config.local_addr,
        **config.rdzv_configs,
    )

    master_addr, master_port = _get_addr_and_port(rdzv_parameters)

    # Set the signals to handle in the environment variable
    os.environ["TORCHELASTIC_SIGNALS_TO_HANDLE"] = config.signals_to_handle

    # Start health check server before rendezvous so TW sees a healthy
    # thrift port during the potentially long MAST rendezvous store barrier
    # (10-22+ min for large jobs).  The _AliveCallbackProxy returns
    # time.time() until wired to the agent after construction.
    # Skip if a server was already provided by the caller (e.g. started
    # before remote_pre_launch in the APF executor).
    if health_check_server is None:
        healthcheck_port = os.getenv(TORCHELASTIC_HEALTH_CHECK_PORT)
        if healthcheck_port is not None and justknobs_check(
            "ai_infra/pytorch_distributed:torchelastic_enable_healthcheck_before_rendezvous",
            default=False,
        ):
            try:
                health_check_server = create_healthcheck_server(
                    alive_callback=_AliveCallbackProxy(),
                    port=int(healthcheck_port),
                    timeout=60,
                )
                health_check_server.start()
                logger.info(
                    "Started early health check server on port %s before rendezvous",
                    healthcheck_port,
                )
            except Exception:
                logger.warning(
                    "Failed to start early health check server", exc_info=True
                )
                health_check_server = None

    spec = WorkerSpec(
        role=config.role,
        local_world_size=config.nproc_per_node,
        entrypoint=entrypoint,
        args=tuple(args),
        rdzv_handler=rdzv_registry.get_rendezvous_handler(rdzv_parameters),
        max_restarts=config.max_restarts,
        monitor_interval=config.monitor_interval,
        master_addr=master_addr,
        master_port=master_port,
        local_addr=config.local_addr,
        event_log_handler=config.event_log_handler,
        numa_options=config.numa_options,
        duplicate_stdout_filters=config.duplicate_stdout_filters,
        duplicate_stderr_filters=config.duplicate_stderr_filters,
        virtual_local_rank=config.virtual_local_rank,
    )

    agent = LocalElasticAgent(
        spec=spec,
        logs_specs=config.logs_specs,  # type: ignore[arg-type]
        start_method=config.start_method,
        log_line_prefix_template=config.log_line_prefix_template,
        shutdown_timeout=config.shutdown_timeout,  # type: ignore[arg-type]
        health_check_server=health_check_server,
    )

    if health_check_server is not None:
        cb = health_check_server.alive_callback
        if isinstance(cb, _AliveCallbackProxy):
            cb.set_delegate(agent._get_alive_time)

    shutdown_rdzv = True
    try:
        metrics.initialize_metrics(metrics.MetricsConfig(config.metrics_cfg))

        result = agent.run()
        # records that agent.run() has succeeded NOT that workers have succeeded
        events.record(agent.get_event_succeeded(), config.event_log_handler)

        if result.is_failed():
            # ChildFailedError is treated specially by @record
            # if the error files for the failed children exist
            # @record will copy the first error (root cause)
            # to the error file of the launcher process.
            raise ChildFailedError(
                name=entrypoint_name,
                failures=result.failures,
            )

        return result.return_values
    except ChildFailedError:
        raise
    except SignalException:
        # when the agent dies with a signal do NOT shutdown the rdzv_handler
        # since this closes the rendezvous on this rdzv_id permanently and
        # prevents any additional scaling events
        shutdown_rdzv = False
        events.record(agent.get_event_failed(), config.event_log_handler)
        raise
    except Exception:
        events.record(agent.get_event_failed(), config.event_log_handler)
        raise
    finally:
        if shutdown_rdzv:
            spec.rdzv_handler.shutdown()