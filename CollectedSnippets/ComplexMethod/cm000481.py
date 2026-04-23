def _build_node_execution_where_clause(
    graph_exec_id: str | None = None,
    node_id: str | None = None,
    block_ids: list[str] | None = None,
    statuses: list[ExecutionStatus] | None = None,
    created_time_gte: datetime | None = None,
    created_time_lte: datetime | None = None,
) -> AgentNodeExecutionWhereInput:
    """
    Build where clause for node execution queries.
    """
    where_clause: AgentNodeExecutionWhereInput = {}
    if graph_exec_id:
        where_clause["agentGraphExecutionId"] = graph_exec_id
    if node_id:
        where_clause["agentNodeId"] = node_id
    if block_ids:
        where_clause["Node"] = {"is": {"agentBlockId": {"in": block_ids}}}
    if statuses:
        where_clause["OR"] = [{"executionStatus": status} for status in statuses]

    if created_time_gte or created_time_lte:
        where_clause["addedTime"] = {
            "gte": created_time_gte or datetime.min.replace(tzinfo=timezone.utc),
            "lte": created_time_lte or datetime.max.replace(tzinfo=timezone.utc),
        }

    return where_clause