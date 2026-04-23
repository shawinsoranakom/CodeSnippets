def retrieve_result_from_completion_queue(
    process: torch.multiprocessing.Process,
    completion_queue: torch.multiprocessing.Queue,
    timeout: int | None = None,
) -> Any:
    """Get result from the completion_queue associated with process.

    When the process finished without putting a result or the timeout expired an exception instance will be returned"""
    queue_timeout = 120 if timeout is None else max(10, min(120, timeout // 4))
    start_time = time.time()
    # Periodically check the process for liveness
    while True:
        try:
            return completion_queue.get(timeout=queue_timeout)
        except queue.Empty:
            # If the process is no longer alive we cannot get a result from the queue unless it is there right now.
            # This can happen if the timeout occurred just before the process put its result and terminated.
            # So do a last check for emptiness before considering it as a failure.
            if not process.is_alive() and completion_queue.empty():
                return RuntimeError(f"Exited with {process.exitcode}")
        if timeout is not None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                return RuntimeError(f"Process timed out out after {elapsed}s")