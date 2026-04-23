async def update_search(user_id: str, search: SearchEntry) -> str:
    """
    Upsert a search request for the user and return the search ID.
    """
    if search.search_id:
        # Update existing search
        await prisma.models.BuilderSearchHistory.prisma().update(
            where={
                "id": search.search_id,
            },
            data={
                "searchQuery": search.search_query or "",
                "filter": search.filter or [],  # type: ignore
                "byCreator": search.by_creator or [],
            },
        )
        return search.search_id
    else:
        # Create new search
        new_search = await prisma.models.BuilderSearchHistory.prisma().create(
            data={
                "userId": user_id,
                "searchQuery": search.search_query or "",
                "filter": search.filter or [],  # type: ignore
                "byCreator": search.by_creator or [],
            }
        )
        return new_search.id
