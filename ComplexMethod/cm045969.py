def _stop_spawn_managed_process(
    process: multiprocessing.process.BaseProcess | None,
    *,
    process_group_id: int | None,
    shutdown_timeout_seconds: float,
) -> None:
    if process is None and process_group_id is None:
        return

    if process_group_id is None:
        if process is None or process.exitcode is not None:
            return

        process.terminate()
        process.join(timeout=shutdown_timeout_seconds)

        if process.exitcode is not None:
            return

        process.kill()
        process.join(timeout=shutdown_timeout_seconds)

        if process.exitcode is None:
            logger.warning(
                "Managed MinerU spawn process {} did not exit after forceful stop.",
                process.pid,
            )
        return

    if process is not None and process.exitcode is None:
        process.terminate()
        process.join(timeout=shutdown_timeout_seconds)

    cleanup_process_tree_descendants_by_pid(process_group_id)

    if process is not None:
        process.join(timeout=shutdown_timeout_seconds)
        if process.exitcode is None:
            logger.warning(
                "Managed MinerU spawn process {} did not exit after forceful stop.",
                process.pid,
            )