async def stop_graph_execution(
    user_id: str,
    graph_exec_id: str,
    wait_timeout: float = 15.0,
    cascade: bool = True,
):
    """
    Stop a graph execution and optionally all its child executions.

    Mechanism:
    1. Set the cancel event for this execution
    2. If cascade=True, recursively stop all child executions
    3. Graph executor's cancel handler thread detects the event, terminates workers,
       reinitializes worker pool, and returns.
    4. Update execution statuses in DB and set `error` outputs to `"TERMINATED"`.

    Args:
        user_id: User ID who owns the execution
        graph_exec_id: Graph execution ID to stop
        wait_timeout: Maximum time to wait for execution to stop (seconds)
        cascade: If True, recursively stop all child executions
    """
    queue_client = await get_async_execution_queue()
    db = execution_db if prisma.is_connected() else get_database_manager_async_client()

    # First, find and stop all child executions if cascading
    if cascade:
        children = await _get_child_executions(graph_exec_id)
        logger.info(
            f"Stopping {len(children)} child executions of execution {graph_exec_id}"
        )

        # Stop all children in parallel (recursively, with cascading enabled)
        if children:
            await asyncio.gather(
                *[
                    stop_graph_execution(
                        user_id=user_id,
                        graph_exec_id=child.id,
                        wait_timeout=wait_timeout,
                        cascade=True,  # Recursively cascade to grandchildren
                    )
                    for child in children
                ],
                return_exceptions=True,  # Don't fail parent stop if child stop fails
            )

    # Now stop this execution
    await queue_client.publish_message(
        routing_key="",
        message=CancelExecutionEvent(graph_exec_id=graph_exec_id).model_dump_json(),
        exchange=GRAPH_EXECUTION_CANCEL_EXCHANGE,
    )

    if not wait_timeout:
        return

    start_time = time.time()
    while time.time() - start_time < wait_timeout:
        graph_exec = await db.get_graph_execution_meta(
            execution_id=graph_exec_id, user_id=user_id
        )

        if not graph_exec:
            raise NotFoundError(f"Graph execution #{graph_exec_id} not found.")

        if graph_exec.status in [
            ExecutionStatus.TERMINATED,
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
        ]:
            # If graph execution is terminated/completed/failed, cancellation is complete
            await get_async_execution_event_bus().publish(graph_exec)
            return

        if graph_exec.status in [
            ExecutionStatus.QUEUED,
            ExecutionStatus.INCOMPLETE,
            ExecutionStatus.REVIEW,
        ]:
            # If the graph is queued/incomplete/paused for review, terminate immediately
            # No need to wait for executor since it's not actively running

            # If graph is in REVIEW status, clean up pending reviews before terminating
            if graph_exec.status == ExecutionStatus.REVIEW:
                # Use human_review_db if Prisma connected, else database manager
                review_db = (
                    human_review_db
                    if prisma.is_connected()
                    else get_database_manager_async_client()
                )
                # Mark all pending reviews as rejected/cancelled
                cancelled_count = await review_db.cancel_pending_reviews_for_execution(
                    graph_exec_id, user_id
                )
                logger.info(
                    f"Cancelled {cancelled_count} pending review(s) for stopped execution {graph_exec_id}"
                )

            graph_exec.status = ExecutionStatus.TERMINATED

            await asyncio.gather(
                # Update graph execution status
                db.update_graph_execution_stats(
                    graph_exec_id=graph_exec.id,
                    status=ExecutionStatus.TERMINATED,
                ),
                # Publish graph execution event
                get_async_execution_event_bus().publish(graph_exec),
            )
            return

        if graph_exec.status == ExecutionStatus.RUNNING:
            await asyncio.sleep(0.1)

    raise TimeoutError(
        f"Graph execution #{graph_exec_id} will need to take longer than {wait_timeout} seconds to stop. "
        f"You can check the status of the execution in the UI or try again later."
    )