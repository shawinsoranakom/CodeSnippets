async def search(
    user_id: Annotated[str, fastapi.Security(get_user_id)],
    search_query: Annotated[str | None, fastapi.Query()] = None,
    filter: Annotated[list[builder_model.FilterType] | None, fastapi.Query()] = None,
    search_id: Annotated[str | None, fastapi.Query()] = None,
    by_creator: Annotated[list[str] | None, fastapi.Query()] = None,
    page: Annotated[int, fastapi.Query()] = 1,
    page_size: Annotated[int, fastapi.Query()] = 50,
) -> builder_model.SearchResponse:
    """
    Search for blocks (including integrations), marketplace agents, and user library agents.
    """
    # If no filters are provided, then we will return all types
    if not filter:
        filter = [
            "blocks",
            "integrations",
            "marketplace_agents",
            "my_agents",
        ]
    search_query = sanitize_query(search_query)

    # Get all possible results
    cached_results = await builder_db.get_sorted_search_results(
        user_id=user_id,
        search_query=search_query,
        filters=filter,
        by_creator=by_creator,
    )

    # Paginate results
    total_combined_items = len(cached_results.items)
    pagination = Pagination(
        total_items=total_combined_items,
        total_pages=(total_combined_items + page_size - 1) // page_size,
        current_page=page,
        page_size=page_size,
    )

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = cached_results.items[start_idx:end_idx]

    # Update the search entry by id
    search_id = await builder_db.update_search(
        user_id,
        builder_model.SearchEntry(
            search_query=search_query,
            filter=filter,
            by_creator=by_creator,
            search_id=search_id,
        ),
    )

    return builder_model.SearchResponse(
        items=paginated_items,
        search_id=search_id,
        total_items=cached_results.total_items,
        pagination=pagination,
    )
