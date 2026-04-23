def stop_managed_process(
    process: subprocess.Popen[bytes] | None,
    *,
    process_group_id: int | None = None,
    shutdown_timeout_seconds: float,
    use_stdin_shutdown_watcher: bool,
) -> None:
    if process is None and process_group_id is None:
        return

    if process is None:
        cleanup_process_tree_descendants_by_pid(process_group_id)
        return

    resolved_process_group_id = process_group_id if process_group_id is not None else process.pid
    was_running_at_entry = process.poll() is None
    exited_via_stdin_eof = False
    tree_signaled = False

    if not was_running_at_entry:
        cleanup_process_tree_descendants_by_pid(process_group_id)
        return

    if use_stdin_shutdown_watcher:
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        try:
            process.wait(timeout=shutdown_timeout_seconds)
            exited_via_stdin_eof = True
        except subprocess.TimeoutExpired:
            logger.debug(
                "Managed MinerU process did not stop after stdin EOF within {}s. Falling back to process-tree termination.",
                shutdown_timeout_seconds,
            )

    if process.poll() is None:
        _signal_process_tree_pid(resolved_process_group_id, force=False)
        tree_signaled = True
        try:
            process.wait(timeout=shutdown_timeout_seconds)
        except subprocess.TimeoutExpired:
            pass

    if process.poll() is None:
        _signal_process_tree_pid(resolved_process_group_id, force=True)
        tree_signaled = True
        try:
            process.wait(timeout=shutdown_timeout_seconds)
        except subprocess.TimeoutExpired:
            logger.warning(
                "Managed MinerU process {} did not exit after forceful stop.",
                process.pid,
            )

    if exited_via_stdin_eof and not tree_signaled:
        cleanup_process_tree_descendants_by_pid(resolved_process_group_id)