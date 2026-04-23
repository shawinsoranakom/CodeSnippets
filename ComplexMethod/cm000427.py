def _build_prisma_where(
    start: datetime | None,
    end: datetime | None,
    provider: str | None,
    user_id: str | None,
    model: str | None = None,
    block_name: str | None = None,
    tracking_type: str | None = None,
    graph_exec_id: str | None = None,
) -> PlatformCostLogWhereInput:
    """Build a Prisma WhereInput for PlatformCostLog filters."""
    where: PlatformCostLogWhereInput = {}

    if start and end:
        where["createdAt"] = {"gte": start, "lte": end}
    elif start:
        where["createdAt"] = {"gte": start}
    elif end:
        where["createdAt"] = {"lte": end}

    if provider:
        where["provider"] = provider.lower()

    if user_id:
        where["userId"] = user_id

    if model:
        where["model"] = model

    if block_name:
        # Case-insensitive match — mirrors the original LOWER() SQL filter.
        where["blockName"] = {"equals": block_name, "mode": "insensitive"}

    if tracking_type:
        where["trackingType"] = tracking_type

    if graph_exec_id:
        where["graphExecId"] = graph_exec_id

    return where