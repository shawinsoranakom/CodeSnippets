async def get_graph_executions_count(
    user_id: Optional[str] = None,
    graph_id: Optional[str] = None,
    statuses: Optional[list[ExecutionStatus]] = None,
    created_time_gte: Optional[datetime] = None,
    created_time_lte: Optional[datetime] = None,
    started_time_gte: Optional[datetime] = None,
    started_time_lte: Optional[datetime] = None,
    updated_time_gte: Optional[datetime] = None,
    updated_time_lte: Optional[datetime] = None,
) -> int:
    """
    Get count of graph executions with optional filters.

    Args:
        user_id: Optional user ID to filter by
        graph_id: Optional graph ID to filter by
        statuses: Optional list of execution statuses to filter by
        created_time_gte: Optional minimum creation time
        created_time_lte: Optional maximum creation time
        started_time_gte: Optional minimum start time (when execution started running)
        started_time_lte: Optional maximum start time (when execution started running)
        updated_time_gte: Optional minimum update time
        updated_time_lte: Optional maximum update time

    Returns:
        Count of matching graph executions
    """
    where_filter: AgentGraphExecutionWhereInput = {
        "isDeleted": False,
    }

    if user_id:
        where_filter["userId"] = user_id

    if graph_id:
        where_filter["agentGraphId"] = graph_id

    if created_time_gte or created_time_lte:
        where_filter["createdAt"] = {
            "gte": created_time_gte or datetime.min.replace(tzinfo=timezone.utc),
            "lte": created_time_lte or datetime.max.replace(tzinfo=timezone.utc),
        }

    if started_time_gte or started_time_lte:
        where_filter["startedAt"] = {
            "gte": started_time_gte or datetime.min.replace(tzinfo=timezone.utc),
            "lte": started_time_lte or datetime.max.replace(tzinfo=timezone.utc),
        }

    if updated_time_gte or updated_time_lte:
        where_filter["updatedAt"] = {
            "gte": updated_time_gte or datetime.min.replace(tzinfo=timezone.utc),
            "lte": updated_time_lte or datetime.max.replace(tzinfo=timezone.utc),
        }

    if statuses:
        where_filter["OR"] = [{"executionStatus": status} for status in statuses]

    count = await AgentGraphExecution.prisma().count(where=where_filter)
    return count