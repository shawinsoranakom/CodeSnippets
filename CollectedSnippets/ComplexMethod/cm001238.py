async def get_store_agents(
    featured: bool = False,
    creators: list[str] | None = None,
    sorted_by: StoreAgentsSortOptions | None = None,
    search_query: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> store_model.StoreAgentsResponse:
    """
    Get PUBLIC store agents from the StoreAgent view.

    Search behavior:
    - With search_query: Uses hybrid search (semantic + lexical)
    - Fallback: If embeddings unavailable, gracefully degrades to lexical-only
    - Rationale: User-facing endpoint prioritizes availability over accuracy

    Note: Admin operations (approval) use fail-fast to prevent inconsistent state.
    """
    logger.debug(
        "Getting store agents: "
        f"featured={featured}, creators={creators}, sorted_by={sorted_by}, "
        f"query={search_query}, category={category}, page={page}"
    )

    search_used_hybrid = False
    store_agents: list[store_model.StoreAgent] = []
    agents: list[dict[str, Any]] = []
    total = 0
    total_pages = 0

    try:
        # If search_query is provided, use hybrid search (embeddings + tsvector)
        if search_query:
            # Try hybrid search combining semantic and lexical signals
            # Falls back to lexical-only if OpenAI unavailable (user-facing, high SLA)
            try:
                agents, total = await hybrid_search(
                    query=search_query,
                    featured=featured,
                    creators=creators,
                    category=category,
                    sorted_by="relevance",  # Use hybrid scoring for relevance
                    page=page,
                    page_size=page_size,
                )
                search_used_hybrid = True
            except Exception as e:
                # Log error but fall back to lexical search for better UX
                logger.error(
                    f"Hybrid search failed (likely OpenAI unavailable), "
                    f"falling back to lexical search: {e}"
                )
                # search_used_hybrid remains False, will use fallback path below

            # Convert hybrid search results (dict format) if hybrid succeeded
            # Fall through to direct DB search if hybrid returned nothing
            if search_used_hybrid and agents:
                total_pages = (total + page_size - 1) // page_size
                store_agents: list[store_model.StoreAgent] = []
                for agent in agents:
                    try:
                        store_agent = store_model.StoreAgent(
                            slug=agent["slug"],
                            agent_name=agent["agent_name"],
                            agent_image=(
                                agent["agent_image"][0] if agent["agent_image"] else ""
                            ),
                            creator=agent["creator_username"] or "Needs Profile",
                            creator_avatar=agent["creator_avatar"] or "",
                            sub_heading=agent["sub_heading"],
                            description=agent["description"],
                            runs=agent["runs"],
                            rating=agent["rating"],
                            agent_graph_id=agent.get("graph_id", ""),
                        )
                        store_agents.append(store_agent)
                    except Exception as e:
                        logger.error(
                            f"Error parsing Store agent from hybrid search results: {e}"
                        )
                        continue

        if not search_used_hybrid or not agents:
            # Fallback path: direct DB query with optional tsvector search.
            # This mirrors the original pre-hybrid-search implementation.
            store_agents, total = await _fallback_store_agent_search(
                search_query=search_query,
                featured=featured,
                creators=creators,
                category=category,
                sorted_by=sorted_by,
                page=page,
                page_size=page_size,
            )
            total_pages = (total + page_size - 1) // page_size

        logger.debug(f"Found {len(store_agents)} agents")
        return store_model.StoreAgentsResponse(
            agents=store_agents,
            pagination=store_model.Pagination(
                current_page=page,
                total_items=total,
                total_pages=total_pages,
                page_size=page_size,
            ),
        )
    except Exception as e:
        logger.error(f"Error getting store agents: {e}")
        raise DatabaseError("Failed to fetch store agents") from e