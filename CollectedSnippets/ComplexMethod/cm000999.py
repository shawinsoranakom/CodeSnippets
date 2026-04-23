async def wait_for_execution(
    user_id: str,
    graph_id: str,
    execution_id: str,
    timeout_seconds: int,
) -> GraphExecution | None:
    """
    Wait for an execution to reach a terminal or paused status using Redis pubsub.

    Handles the race condition between checking status and subscribing by
    re-checking the DB after the subscription is established.

    Args:
        user_id: User ID
        graph_id: Graph ID
        execution_id: Execution ID to wait for
        timeout_seconds: Max seconds to wait

    Returns:
        The execution with current status, or None if not found
    """
    exec_db = execution_db()

    # Quick check — maybe it's already done
    execution = await exec_db.get_graph_execution(
        user_id=user_id,
        execution_id=execution_id,
        include_node_executions=False,
    )
    if not execution:
        return None

    if execution.status in STOP_WAITING_STATUSES:
        logger.debug(
            f"Execution {execution_id} already in stop-waiting state: "
            f"{execution.status}"
        )
        return execution

    logger.info(
        f"Waiting up to {timeout_seconds}s for execution {execution_id} "
        f"(current status: {execution.status})"
    )

    event_bus = AsyncRedisExecutionEventBus()
    channel_key = f"{user_id}/{graph_id}/{execution_id}"

    # Mutable container so _subscribe_and_wait can surface the task even if
    # asyncio.wait_for cancels the coroutine before it returns.
    task_holder: list[asyncio.Task] = []

    try:
        result = await asyncio.wait_for(
            _subscribe_and_wait(
                event_bus, channel_key, user_id, execution_id, exec_db, task_holder
            ),
            timeout=timeout_seconds,
        )
        return result
    except asyncio.TimeoutError:
        logger.info(f"Timeout waiting for execution {execution_id}")
    except Exception as e:
        logger.error(f"Error waiting for execution: {e}", exc_info=True)
    finally:
        for task in task_holder:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        await event_bus.close()

    # Return current state on timeout/error
    return await exec_db.get_graph_execution(
        user_id=user_id,
        execution_id=execution_id,
        include_node_executions=False,
    )