async def get_recent_searches(user_id: str, limit: int = 5) -> list[SearchEntry]:
    """
    Get the user's most recent search requests.
    """
    searches = await prisma.models.BuilderSearchHistory.prisma().find_many(
        where={
            "userId": user_id,
        },
        order={
            "updatedAt": "desc",
        },
        take=limit,
    )
    return [
        SearchEntry(
            search_query=s.searchQuery,
            filter=s.filter,  # type: ignore
            by_creator=s.byCreator,
            search_id=s.id,
        )
        for s in searches
    ]


async def get_sorted_search_results(
    *,
    user_id: str,
    search_query: str | None,
    filters: Sequence[FilterType],
    by_creator: Sequence[str] | None = None,
) -> _SearchCacheEntry:
    normalized_filters: tuple[FilterType, ...] = tuple(sorted(set(filters or [])))
    normalized_creators: tuple[str, ...] = tuple(sorted(set(by_creator or [])))
    return await _build_cached_search_results(
        user_id=user_id,
        search_query=search_query or "",
        filters=normalized_filters,
        by_creator=normalized_creators,
    )
