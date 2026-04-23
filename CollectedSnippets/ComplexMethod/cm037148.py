def shutdown(procs: list[BaseProcess], timeout: float | None = None) -> None:
    """Shutdown processes with timeout.

    Args:
        procs: List of processes to shutdown
        timeout: Maximum time in seconds to wait for graceful shutdown
    """
    if timeout is None:
        timeout = 0.0

    # Allow at least 5 seconds for remaining procs to terminate.
    timeout = max(timeout, 5.0)

    # Shutdown the process.
    for proc in procs:
        if proc.is_alive():
            proc.terminate()

    # Allow time for remaining procs to terminate.
    deadline = time.monotonic() + timeout
    for proc in procs:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        if proc.is_alive():
            proc.join(remaining)

    for proc in procs:
        if proc.is_alive() and (pid := proc.pid) is not None:
            kill_process_tree(pid)