async def update_graph_execution_stats(
    graph_exec_id: str,
    status: ExecutionStatus | None = None,
    stats: GraphExecutionStats | None = None,
) -> GraphExecution | None:
    if not status and not stats:
        raise ValueError(
            f"Must provide either status or stats to update for execution {graph_exec_id}"
        )

    update_data: AgentGraphExecutionUpdateManyMutationInput = {}

    if stats:
        stats_dict = stats.model_dump()
        if isinstance(stats_dict.get("error"), Exception):
            stats_dict["error"] = str(stats_dict["error"])
        update_data["stats"] = SafeJson(stats_dict)

    if status:
        update_data["executionStatus"] = status
        # Set endedAt when execution reaches a terminal status
        terminal_statuses = [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TERMINATED,
        ]
        if status in terminal_statuses:
            update_data["endedAt"] = datetime.now(tz=timezone.utc)

    where_clause: AgentGraphExecutionWhereInput = {"id": graph_exec_id}

    if status:
        if allowed_from := VALID_STATUS_TRANSITIONS.get(status, []):
            # Add OR clause to check if current status is one of the allowed source statuses
            where_clause["AND"] = [
                {"id": graph_exec_id},
                {"OR": [{"executionStatus": s} for s in allowed_from]},
            ]
        else:
            raise ValueError(
                f"Status {status} cannot be set via update for execution {graph_exec_id}. "
                f"This status can only be set at creation or is not a valid target status."
            )

    await AgentGraphExecution.prisma().update_many(
        where=where_clause,
        data=update_data,
    )

    graph_exec = await AgentGraphExecution.prisma().find_unique_or_raise(
        where={"id": graph_exec_id},
        include=graph_execution_include(
            [*get_io_block_ids(), *get_webhook_block_ids()]
        ),
    )

    return GraphExecution.from_db(graph_exec)