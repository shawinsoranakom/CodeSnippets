async def get_store_creators(
    featured: bool = False,
    search_query: str | None = None,
    sorted_by: StoreCreatorsSortOptions | None = None,
    page: int = 1,
    page_size: int = 20,
) -> store_model.CreatorsResponse:
    """Get PUBLIC store creators from the Creator view"""
    logger.debug(
        "Getting store creators: "
        f"featured={featured}, query={search_query}, sorted_by={sorted_by}, page={page}"
    )

    # Build where clause with sanitized inputs
    where = {}

    if featured:
        where["is_featured"] = featured

    # Add search filter if provided, using parameterized queries
    if search_query:
        # Sanitize and validate search query by escaping special characters
        sanitized_query = search_query.strip()
        if not sanitized_query or len(sanitized_query) > 100:  # Reasonable length limit
            raise DatabaseError("Invalid search query")

        # Escape special SQL characters
        sanitized_query = (
            sanitized_query.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace(";", "\\;")
            .replace("--", "\\--")
            .replace("/*", "\\/*")
            .replace("*/", "\\*/")
        )

        where["OR"] = [
            {"username": {"contains": sanitized_query, "mode": "insensitive"}},
            {"name": {"contains": sanitized_query, "mode": "insensitive"}},
            {"description": {"contains": sanitized_query, "mode": "insensitive"}},
        ]

    try:
        # Validate pagination parameters
        if not isinstance(page, int) or page < 1:
            raise DatabaseError("Invalid page number")
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise DatabaseError("Invalid page size")

        # Get total count for pagination using sanitized where clause
        total = await prisma.models.Creator.prisma().count(
            where=prisma.types.CreatorWhereInput(**where)
        )
        total_pages = (total + page_size - 1) // page_size

        # Add pagination with validated parameters
        skip = (page - 1) * page_size
        take = page_size

        order: prisma.types.CreatorOrderByInput = (
            {"agent_rating": "desc"}
            if sorted_by == StoreCreatorsSortOptions.AGENT_RATING
            else (
                {"agent_runs": "desc"}
                if sorted_by == StoreCreatorsSortOptions.AGENT_RUNS
                else (
                    {"num_agents": "desc"}
                    if sorted_by == StoreCreatorsSortOptions.NUM_AGENTS
                    else {"username": "asc"}
                )
            )
        )

        # Execute query with sanitized parameters
        creators = await prisma.models.Creator.prisma().find_many(
            where=prisma.types.CreatorWhereInput(**where),
            skip=skip,
            take=take,
            order=order,
        )

        # Convert to response model
        creator_models = [
            store_model.CreatorDetails.from_db(creator) for creator in creators
        ]

        logger.debug(f"Found {len(creator_models)} creators")
        return store_model.CreatorsResponse(
            creators=creator_models,
            pagination=store_model.Pagination(
                current_page=page,
                total_items=total,
                total_pages=total_pages,
                page_size=page_size,
            ),
        )
    except Exception as e:
        logger.error(f"Error getting store creators: {e}")
        raise DatabaseError("Failed to fetch store creators") from e