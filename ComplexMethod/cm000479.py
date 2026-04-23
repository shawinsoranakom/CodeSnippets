async def get_graph_executions_paginated(
    user_id: str,
    graph_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    statuses: Optional[list[ExecutionStatus]] = None,
    created_time_gte: Optional[datetime] = None,
    created_time_lte: Optional[datetime] = None,
) -> GraphExecutionsPaginated:
    """Get paginated graph executions for a specific graph."""
    where_filter: AgentGraphExecutionWhereInput = {
        "isDeleted": False,
        "userId": user_id,
    }

    if graph_id:
        where_filter["agentGraphId"] = graph_id
    if created_time_gte or created_time_lte:
        where_filter["createdAt"] = {
            "gte": created_time_gte or datetime.min.replace(tzinfo=timezone.utc),
            "lte": created_time_lte or datetime.max.replace(tzinfo=timezone.utc),
        }
    if statuses:
        where_filter["OR"] = [{"executionStatus": status} for status in statuses]

    total_count = await AgentGraphExecution.prisma().count(where=where_filter)
    total_pages = (total_count + page_size - 1) // page_size

    offset = (page - 1) * page_size
    executions = await AgentGraphExecution.prisma().find_many(
        where=where_filter,
        order={"createdAt": "desc"},
        take=page_size,
        skip=offset,
    )

    return GraphExecutionsPaginated(
        executions=[GraphExecutionMeta.from_db(execution) for execution in executions],
        pagination=Pagination(
            total_items=total_count,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        ),
    )