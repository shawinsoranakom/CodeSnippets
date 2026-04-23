async def _fallback_store_agent_search(
    *,
    search_query: str | None,
    featured: bool,
    creators: list[str] | None,
    category: str | None,
    sorted_by: StoreAgentsSortOptions | None,
    page: int,
    page_size: int,
) -> tuple[list[store_model.StoreAgent], int]:
    """Direct DB search fallback when hybrid search is unavailable or empty.

    Uses ad-hoc to_tsvector/plainto_tsquery with ts_rank_cd for text search,
    matching the quality of the original pre-hybrid-search implementation.
    Falls back to simple listing when no search query is provided.
    """
    if not search_query:
        # No search query — use Prisma for simple filtered listing
        where_clause: prisma.types.StoreAgentWhereInput = {"is_available": True}
        if featured:
            where_clause["featured"] = featured
        if creators:
            where_clause["creator_username"] = {"in": creators}
        if category:
            where_clause["categories"] = {"has": category}

        order_by = []
        if sorted_by == StoreAgentsSortOptions.RATING:
            order_by.append({"rating": "desc"})
        elif sorted_by == StoreAgentsSortOptions.RUNS:
            order_by.append({"runs": "desc"})
        elif sorted_by == StoreAgentsSortOptions.NAME:
            order_by.append({"agent_name": "asc"})
        elif sorted_by == StoreAgentsSortOptions.UPDATED_AT:
            order_by.append({"updated_at": "desc"})

        db_agents = await prisma.models.StoreAgent.prisma().find_many(
            where=where_clause,
            order=order_by,
            skip=(page - 1) * page_size,
            take=page_size,
        )
        total = await prisma.models.StoreAgent.prisma().count(where=where_clause)
        return [store_model.StoreAgent.from_db(a) for a in db_agents], total

    # Text search using ad-hoc tsvector on StoreAgent view fields
    params: list[Any] = [search_query]
    filters = ["sa.is_available = true"]
    param_idx = 2

    if featured:
        filters.append("sa.featured = true")
    if creators:
        params.append(creators)
        filters.append(f"sa.creator_username = ANY(${param_idx})")
        param_idx += 1
    if category:
        params.append(category)
        filters.append(f"${param_idx} = ANY(sa.categories)")
        param_idx += 1

    where_sql = " AND ".join(filters)

    params.extend([page_size, (page - 1) * page_size])
    limit_param = f"${param_idx}"
    param_idx += 1
    offset_param = f"${param_idx}"

    sql = f"""
        WITH ranked AS (
            SELECT sa.*,
                ts_rank_cd(
                    to_tsvector('english',
                        COALESCE(sa.agent_name, '') || ' ' ||
                        COALESCE(sa.sub_heading, '') || ' ' ||
                        COALESCE(sa.description, '')
                    ),
                    plainto_tsquery('english', $1)
                ) AS rank,
                COUNT(*) OVER () AS total_count
            FROM {{schema_prefix}}"StoreAgent" sa
            WHERE {where_sql}
            AND to_tsvector('english',
                    COALESCE(sa.agent_name, '') || ' ' ||
                    COALESCE(sa.sub_heading, '') || ' ' ||
                    COALESCE(sa.description, '')
                ) @@ plainto_tsquery('english', $1)
        )
        SELECT * FROM ranked
        ORDER BY rank DESC
        LIMIT {limit_param} OFFSET {offset_param}
    """

    results = await query_raw_with_schema(sql, *params)
    total = results[0]["total_count"] if results else 0

    store_agents = []
    for row in results:
        try:
            store_agents.append(
                store_model.StoreAgent(
                    slug=row["slug"],
                    agent_name=row["agent_name"],
                    agent_image=row["agent_image"][0] if row["agent_image"] else "",
                    creator=row["creator_username"] or "Needs Profile",
                    creator_avatar=row["creator_avatar"] or "",
                    sub_heading=row["sub_heading"],
                    description=row["description"],
                    runs=row["runs"],
                    rating=row["rating"],
                    agent_graph_id=row.get("graph_id", ""),
                )
            )
        except Exception as e:
            logger.error(f"Error parsing StoreAgent from fallback search: {e}")
            continue

    return store_agents, total