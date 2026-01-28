async def _build_cached_search_results(
    user_id: str,
    search_query: str,
    filters: tuple[FilterType, ...],
    by_creator: tuple[str, ...],
) -> _SearchCacheEntry:
    normalized_query = (search_query or "").strip().lower()

    include_blocks = "blocks" in filters
    include_integrations = "integrations" in filters
    include_library_agents = "my_agents" in filters
    include_marketplace_agents = "marketplace_agents" in filters

    scored_items: list[_ScoredItem] = []
    total_items: dict[FilterType, int] = {
        "blocks": 0,
        "integrations": 0,
        "marketplace_agents": 0,
        "my_agents": 0,
    }

    block_results, block_total, integration_total = _collect_block_results(
        normalized_query=normalized_query,
        include_blocks=include_blocks,
        include_integrations=include_integrations,
    )
    scored_items.extend(block_results)
    total_items["blocks"] = block_total
    total_items["integrations"] = integration_total

    if include_library_agents:
        library_response = await library_db.list_library_agents(
            user_id=user_id,
            search_term=search_query or None,
            page=1,
            page_size=MAX_LIBRARY_AGENT_RESULTS,
        )
        total_items["my_agents"] = library_response.pagination.total_items
        scored_items.extend(
            _build_library_items(
                agents=library_response.agents,
                normalized_query=normalized_query,
            )
        )

    if include_marketplace_agents:
        marketplace_response = await store_db.get_store_agents(
            creators=list(by_creator) or None,
            search_query=search_query or None,
            page=1,
            page_size=MAX_MARKETPLACE_AGENT_RESULTS,
        )
        total_items["marketplace_agents"] = marketplace_response.pagination.total_items
        scored_items.extend(
            _build_marketplace_items(
                agents=marketplace_response.agents,
                normalized_query=normalized_query,
            )
        )

    sorted_items = sorted(
        scored_items,
        key=lambda entry: (-entry.score, entry.sort_key, entry.filter_type),
    )

    return _SearchCacheEntry(
        items=[entry.item for entry in sorted_items],
        total_items=total_items,
    )
