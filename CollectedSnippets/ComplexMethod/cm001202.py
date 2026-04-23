async def list_library_agents(
    user_id: str,
    search_term: Optional[str] = None,
    sort_by: library_model.LibraryAgentSort = library_model.LibraryAgentSort.UPDATED_AT,
    page: int = 1,
    page_size: int = 50,
    include_executions: bool = False,
    folder_id: Optional[str] = None,
    include_root_only: bool = False,
) -> library_model.LibraryAgentResponse:
    """
    Retrieves a paginated list of LibraryAgent records for a given user.

    Args:
        user_id: The ID of the user whose LibraryAgents we want to retrieve.
        search_term: Optional string to filter agents by name/description.
        sort_by: Sorting field (createdAt, updatedAt, isFavorite, isCreatedByUser).
        page: Current page (1-indexed).
        page_size: Number of items per page.
        folder_id: Filter by folder ID. If provided, only returns agents in this folder.
        include_root_only: If True, only returns agents without a folder (root-level).
        include_executions: Whether to include execution data for status calculation.
            Defaults to False for performance (UI fetches status separately).
            Set to True when accurate status/metrics are needed (e.g., agent generator).

    Returns:
        A LibraryAgentResponse containing the list of agents and pagination details.

    Raises:
        DatabaseError: If there is an issue fetching from Prisma.
    """
    logger.debug(
        f"Fetching library agents for user_id={user_id}, "
        f"search_term={repr(search_term)}, "
        f"sort_by={sort_by}, page={page}, page_size={page_size}"
    )

    if page < 1 or page_size < 1:
        logger.warning(f"Invalid pagination: page={page}, page_size={page_size}")
        raise InvalidInputError("Invalid pagination input")

    if search_term and len(search_term.strip()) > 100:
        logger.warning(f"Search term too long: {repr(search_term)}")
        raise InvalidInputError("Search term is too long")

    where_clause: prisma.types.LibraryAgentWhereInput = {
        "userId": user_id,
        "isDeleted": False,
        "isArchived": False,
    }

    # Apply folder filter (skip when searching — search spans all folders)
    if folder_id is not None and not search_term:
        where_clause["folderId"] = folder_id
    elif include_root_only and not search_term:
        where_clause["folderId"] = None

    # Build search filter if applicable
    if search_term:
        where_clause["OR"] = [
            {
                "AgentGraph": {
                    "is": {"name": {"contains": search_term, "mode": "insensitive"}}
                }
            },
            {
                "AgentGraph": {
                    "is": {
                        "description": {"contains": search_term, "mode": "insensitive"}
                    }
                }
            },
        ]

    order_by: prisma.types.LibraryAgentOrderByInput | None = None

    if sort_by == library_model.LibraryAgentSort.CREATED_AT:
        order_by = {"createdAt": "asc"}
    elif sort_by == library_model.LibraryAgentSort.UPDATED_AT:
        order_by = {"updatedAt": "desc"}

    library_agents = await prisma.models.LibraryAgent.prisma().find_many(
        where=where_clause,
        include=library_agent_include(
            user_id, include_nodes=False, include_executions=include_executions
        ),
        order=order_by,
        skip=(page - 1) * page_size,
        take=page_size,
    )
    agent_count = await prisma.models.LibraryAgent.prisma().count(where=where_clause)

    logger.debug(f"Retrieved {len(library_agents)} library agents for user #{user_id}")

    graph_ids = [a.agentGraphId for a in library_agents if a.agentGraphId]
    execution_counts, schedule_info = await asyncio.gather(
        _fetch_execution_counts(user_id, graph_ids),
        _fetch_schedule_info(user_id),
    )

    # Only pass valid agents to the response
    valid_library_agents: list[library_model.LibraryAgent] = []

    for agent in library_agents:
        try:
            library_agent = library_model.LibraryAgent.from_db(
                agent,
                execution_count_override=execution_counts.get(agent.agentGraphId),
                schedule_info=schedule_info,
            )
            valid_library_agents.append(library_agent)
        except Exception as e:
            # Skip this agent if there was an error
            logger.error(f"Error parsing LibraryAgent #{agent.id} from DB item: {e}")
            continue

    # Return the response with only valid agents
    return library_model.LibraryAgentResponse(
        agents=valid_library_agents,
        pagination=Pagination(
            total_items=agent_count,
            total_pages=(agent_count + page_size - 1) // page_size,
            current_page=page,
            page_size=page_size,
        ),
    )