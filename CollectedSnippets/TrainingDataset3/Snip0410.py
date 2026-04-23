async def generate_execution_analytics(
    request: ExecutionAnalyticsRequest,
    admin_user_id: str = Security(get_user_id),
):
    """
    Generate activity summaries and correctness scores for graph executions.

    This endpoint:
    1. Fetches all completed executions matching the criteria
    2. Identifies executions missing activity_status or correctness_score
    3. Generates missing data using AI in batches
    4. Updates the database with new stats
    5. Returns a detailed report of the analytics operation
    """
    logger.info(
        f"Admin user {admin_user_id} starting execution analytics generation for graph {request.graph_id}"
    )

    try:
        # Get database client
        db_client = get_db_async_client()

        # Fetch executions to process
        executions = await get_graph_executions(
            graph_id=request.graph_id,
            graph_version=request.graph_version,
            user_id=request.user_id,
            created_time_gte=request.created_after,
            statuses=[
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.TERMINATED,
            ],  # Only process finished executions
        )

        logger.info(
            f"Found {len(executions)} total executions for graph {request.graph_id}"
        )

        # Filter executions that need analytics generation
        executions_to_process = []
        for execution in executions:
            # Skip if we should skip existing analytics and both activity_status and correctness_score exist
            if (
                request.skip_existing
                and execution.stats
                and execution.stats.activity_status
                and execution.stats.correctness_score is not None
            ):
                continue

            # Add execution to processing list
            executions_to_process.append(execution)

        logger.info(
            f"Found {len(executions_to_process)} executions needing analytics generation"
        )

        # Create results for ALL executions - processed and skipped
        results = []
        successful_count = 0
        failed_count = 0

        # Process executions that need analytics generation
        if executions_to_process:
            total_batches = len(
                range(0, len(executions_to_process), request.batch_size)
            )

            for batch_idx, i in enumerate(
                range(0, len(executions_to_process), request.batch_size)
            ):
                batch = executions_to_process[i : i + request.batch_size]
                logger.info(
                    f"Processing batch {batch_idx + 1}/{total_batches} with {len(batch)} executions"
                )

                batch_results = await _process_batch(batch, request, db_client)

                for result in batch_results:
                    results.append(result)
                    if result.status == "success":
                        successful_count += 1
                    elif result.status == "failed":
                        failed_count += 1

                # Small delay between batches to avoid overwhelming the LLM API
                if batch_idx < total_batches - 1:  # Don't delay after the last batch
                    await asyncio.sleep(2)

        # Add ALL executions to results (both processed and skipped)
        for execution in executions:
            # Skip if already processed (added to results above)
            if execution in executions_to_process:
                continue

            results.append(
                ExecutionAnalyticsResult(
                    agent_id=execution.graph_id,
                    version_id=execution.graph_version,
                    user_id=execution.user_id,
                    exec_id=execution.id,
                    summary_text=(
                        execution.stats.activity_status if execution.stats else None
                    ),
                    score=(
                        execution.stats.correctness_score if execution.stats else None
                    ),
                    status="skipped",
                    error_message=None,  # Not an error - just already processed
                    started_at=execution.started_at,
                    ended_at=execution.ended_at,
                )
            )

        response = ExecutionAnalyticsResponse(
            total_executions=len(executions),
            processed_executions=len(executions_to_process),
            successful_analytics=successful_count,
            failed_analytics=failed_count,
            skipped_executions=len(executions) - len(executions_to_process),
            results=results,
        )

        logger.info(
            f"Analytics generation completed: {successful_count} successful, {failed_count} failed, "
            f"{response.skipped_executions} skipped"
        )

        return response

    except Exception as e:
        logger.exception(f"Error during execution analytics generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
