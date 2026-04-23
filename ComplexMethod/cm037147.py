def wait_for_completion_or_failure(
    api_server_manager: APIServerProcessManager,
    engine_manager: Union["CoreEngineProcManager", "CoreEngineActorManager"]
    | None = None,
    coordinator: "DPCoordinator | None" = None,
) -> None:
    """Wait for all processes to complete or detect if any fail.

    Raises an exception if any process exits with a non-zero status.

    Args:
        api_server_manager: The manager for API servers.
        engine_manager: The manager for engine processes.
            If CoreEngineProcManager, it manages local engines;
            if CoreEngineActorManager, it manages all engines.
        coordinator: The coordinator for data parallel.
    """

    try:
        logger.info("Waiting for API servers to complete ...")
        # Create a mapping of sentinels to their corresponding processes
        # for efficient lookup
        sentinel_to_proc: dict[Any, BaseProcess] = {
            proc.sentinel: proc for proc in api_server_manager.processes
        }

        if coordinator:
            sentinel_to_proc[coordinator.proc.sentinel] = coordinator.proc

        if engine_manager:
            core_shutdown_recv, core_shutdown_send = connection.Pipe(duplex=False)

            def monitor_engines():
                try:
                    engine_manager.monitor_engine_liveness()
                finally:
                    core_shutdown_send.close()
                    core_shutdown_recv.close()

            # start monitor for engine liveness
            threading.Thread(target=monitor_engines, daemon=True).start()
            sentinel_to_proc[core_shutdown_recv] = None  # type: ignore[assignment]

        # Check if any process terminates
        while sentinel_to_proc:
            # Wait for any process to terminate (or engine shutdown signal)
            ready_sentinels: list[Any] = connection.wait(sentinel_to_proc)

            # Process any terminated processes
            for sentinel in ready_sentinels:
                proc = sentinel_to_proc.pop(sentinel)

                # Check if process exited with error
                if proc is not None and proc.exitcode != 0:
                    raise RuntimeError(
                        f"Process {proc.name} (PID: {proc.pid}) "
                        f"died with exit code {proc.exitcode}"
                    )
                if engine_manager and engine_manager.failed_proc_name is not None:
                    raise RuntimeError(
                        f"Engine core process {engine_manager.failed_proc_name} "
                        "died unexpectedly."
                    )

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down API servers...")
    except Exception as e:
        logger.exception("Exception occurred while running API servers: %s", str(e))
        raise