async def _process_batch(
    executions, request: ExecutionAnalyticsRequest, db_client
) -> list[ExecutionAnalyticsResult]:
    """Process a batch of executions concurrently."""

    if not settings.secrets.openai_internal_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    async def process_single_execution(execution) -> ExecutionAnalyticsResult:
        try:
            # Generate activity status and score using the specified model
            # Convert stats to GraphExecutionStats if needed
            if execution.stats:
                if isinstance(execution.stats, GraphExecutionMeta.Stats):
                    stats_for_generation = execution.stats.to_db()
                else:
                    # Already GraphExecutionStats
                    stats_for_generation = execution.stats
            else:
                stats_for_generation = GraphExecutionStats()

            activity_response = await generate_activity_status_for_execution(
                graph_exec_id=execution.id,
                graph_id=execution.graph_id,
                graph_version=execution.graph_version,
                execution_stats=stats_for_generation,
                db_client=db_client,
                user_id=execution.user_id,
                execution_status=execution.status,
                model_name=request.model_name,
                skip_feature_flag=True,  # Admin endpoint bypasses feature flags
                system_prompt=request.system_prompt or DEFAULT_SYSTEM_PROMPT,
                user_prompt=request.user_prompt or DEFAULT_USER_PROMPT,
                skip_existing=request.skip_existing,
            )

            if not activity_response:
                return ExecutionAnalyticsResult(
                    agent_id=execution.graph_id,
                    version_id=execution.graph_version,
                    user_id=execution.user_id,
                    exec_id=execution.id,
                    summary_text=None,
                    score=None,
                    status="skipped",
                    error_message="Activity generation returned None",
                    started_at=execution.started_at,
                    ended_at=execution.ended_at,
                )

            # Update the execution stats
            # Convert GraphExecutionMeta.Stats to GraphExecutionStats for DB compatibility
            if execution.stats:
                if isinstance(execution.stats, GraphExecutionMeta.Stats):
                    updated_stats = execution.stats.to_db()
                else:
                    # Already GraphExecutionStats
                    updated_stats = execution.stats
            else:
                updated_stats = GraphExecutionStats()

            updated_stats.activity_status = activity_response["activity_status"]
            updated_stats.correctness_score = activity_response["correctness_score"]

            # Save to database with correct stats type
            await update_graph_execution_stats(
                graph_exec_id=execution.id, stats=updated_stats
            )

            return ExecutionAnalyticsResult(
                agent_id=execution.graph_id,
                version_id=execution.graph_version,
                user_id=execution.user_id,
                exec_id=execution.id,
                summary_text=activity_response["activity_status"],
                score=activity_response["correctness_score"],
                status="success",
                started_at=execution.started_at,
                ended_at=execution.ended_at,
            )

        except Exception as e:
            logger.exception(f"Error processing execution {execution.id}: {e}")
            return ExecutionAnalyticsResult(
                agent_id=execution.graph_id,
                version_id=execution.graph_version,
                user_id=execution.user_id,
                exec_id=execution.id,
                summary_text=None,
                score=None,
                status="failed",
                error_message=str(e),
                started_at=execution.started_at,
                ended_at=execution.ended_at,
            )

    # Process all executions in the batch concurrently
    return await asyncio.gather(
        *[process_single_execution(execution) for execution in executions]
    )
