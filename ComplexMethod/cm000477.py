async def get_graph_executions(
    graph_exec_id: Optional[str] = None,
    execution_ids: Optional[list[str]] = None,
    graph_id: Optional[str] = None,
    graph_version: Optional[int] = None,
    user_id: Optional[str] = None,
    statuses: Optional[list[ExecutionStatus]] = None,
    created_time_gte: Optional[datetime] = None,
    created_time_lte: Optional[datetime] = None,
    started_time_gte: Optional[datetime] = None,
    started_time_lte: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Literal["createdAt", "startedAt", "updatedAt"] = "createdAt",
    order_direction: Literal["asc", "desc"] = "desc",
) -> list[GraphExecutionMeta]:
    """
    Get graph executions with optional filters and ordering.

    ⚠️ **Optional `user_id` check**: MUST USE check in user-facing endpoints.

    Args:
        graph_exec_id: Filter by single execution ID (mutually exclusive with execution_ids)
        execution_ids: Filter by list of execution IDs (mutually exclusive with graph_exec_id)
        order_by: Field to order by. Defaults to "createdAt"
        order_direction: Sort direction. Defaults to "desc"
    """
    where_filter: AgentGraphExecutionWhereInput = {
        "isDeleted": False,
    }
    if graph_exec_id:
        where_filter["id"] = graph_exec_id
    elif execution_ids:
        where_filter["id"] = {"in": execution_ids}

    if user_id:
        where_filter["userId"] = user_id
    if graph_id:
        where_filter["agentGraphId"] = graph_id
    if graph_version is not None:
        where_filter["agentGraphVersion"] = graph_version
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
    if statuses:
        where_filter["OR"] = [{"executionStatus": status} for status in statuses]

    # Build properly typed order clause
    # Prisma wants specific typed dicts for each field, so we construct them explicitly
    order_clause: AgentGraphExecutionOrderByInput
    match (order_by):
        case "startedAt":
            order_clause = {
                "startedAt": order_direction,
            }
        case "updatedAt":
            order_clause = {
                "updatedAt": order_direction,
            }
        case _:
            order_clause = {
                "createdAt": order_direction,
            }

    executions = await AgentGraphExecution.prisma().find_many(
        where=where_filter,
        order=order_clause,
        take=limit,
        skip=offset,
    )
    return [GraphExecutionMeta.from_db(execution) for execution in executions]