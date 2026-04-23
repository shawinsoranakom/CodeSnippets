async def list_presets(
    user_id: str, page: int, page_size: int, graph_id: Optional[str] = None
) -> library_model.LibraryAgentPresetResponse:
    """
    Retrieves a paginated list of AgentPresets for the specified user.

    Args:
        user_id: The user ID whose presets are being retrieved.
        page: The current page index (1-based).
        page_size: Number of items to retrieve per page.
        graph_id: Agent Graph ID to filter by.

    Returns:
        A LibraryAgentPresetResponse containing a list of presets and pagination info.

    Raises:
        DatabaseError: If there's a database error during the operation.
    """
    logger.debug(
        f"Fetching presets for user #{user_id}, page={page}, page_size={page_size}"
    )

    if page < 1 or page_size < 1:
        logger.warning(
            "Invalid pagination input: page=%d, page_size=%d", page, page_size
        )
        raise DatabaseError("Invalid pagination parameters")

    query_filter: prisma.types.AgentPresetWhereInput = {
        "userId": user_id,
        "isDeleted": False,
    }
    if graph_id:
        query_filter["agentGraphId"] = graph_id

    try:
        presets_records = await prisma.models.AgentPreset.prisma().find_many(
            where=query_filter,
            skip=(page - 1) * page_size,
            take=page_size,
            include=AGENT_PRESET_INCLUDE,
        )
        total_items = await prisma.models.AgentPreset.prisma().count(where=query_filter)
        total_pages = (total_items + page_size - 1) // page_size

        presets = [
            library_model.LibraryAgentPreset.from_db(preset)
            for preset in presets_records
        ]

        return library_model.LibraryAgentPresetResponse(
            presets=presets,
            pagination=Pagination(
                total_items=total_items,
                total_pages=total_pages,
                current_page=page,
                page_size=page_size,
            ),
        )

    except prisma.errors.PrismaError as e:
        logger.error(f"Database error getting presets: {e}")
        raise DatabaseError("Failed to fetch presets") from e
