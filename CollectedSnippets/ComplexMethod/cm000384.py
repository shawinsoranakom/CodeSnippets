async def drain_pending_cost_logs(timeout: float = 5.0) -> None:
    """Await all in-flight cost log tasks with a timeout.

    Drains both the executor cost log tasks (_pending_log_tasks in this module,
    used for block execution cost tracking via DatabaseManagerAsyncClient) and
    the copilot cost log tasks (token_tracking._pending_log_tasks, used for
    copilot LLM turns via platform_cost_db()).

    Call this during graceful shutdown to flush pending INSERT tasks before
    the process exits. Tasks that don't complete within `timeout` seconds are
    abandoned and their failures are already logged by _safe_log.
    """
    # asyncio.wait() requires all tasks to belong to the running event loop.
    # _pending_log_tasks is shared across executor worker threads (each with
    # its own loop), so filter to only tasks owned by the current loop.
    # Acquire the lock to take a consistent snapshot (worker threads call
    # discard() via done callbacks concurrently with this iteration).
    current_loop = asyncio.get_running_loop()
    with _pending_log_tasks_lock:
        all_pending = [t for t in _pending_log_tasks if t.get_loop() is current_loop]
    if all_pending:
        logger.info("Draining %d executor cost log task(s)", len(all_pending))
        _, still_pending = await asyncio.wait(all_pending, timeout=timeout)
        if still_pending:
            logger.warning(
                "%d executor cost log task(s) did not complete within %.1fs",
                len(still_pending),
                timeout,
            )
    # Also drain copilot cost log tasks (token_tracking._pending_log_tasks)
    with _copilot_tasks_lock:
        copilot_pending = [t for t in _copilot_tasks if t.get_loop() is current_loop]
    if copilot_pending:
        logger.info("Draining %d copilot cost log task(s)", len(copilot_pending))
        _, still_pending = await asyncio.wait(copilot_pending, timeout=timeout)
        if still_pending:
            logger.warning(
                "%d copilot cost log task(s) did not complete within %.1fs",
                len(still_pending),
                timeout,
            )