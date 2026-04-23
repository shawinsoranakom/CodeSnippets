async def enrich_library_agents_from_steps(
    user_id: str,
    decomposition_result: DecompositionResult | dict[str, Any],
    existing_agents: Sequence[AgentSummary] | Sequence[dict[str, Any]],
    exclude_graph_id: str | None = None,
    include_marketplace: bool = True,
    max_additional_results: int = 10,
) -> list[AgentSummary] | list[dict[str, Any]]:
    """Enrich library agents list with additional searches based on decomposed steps.

    This implements two-phase search: after decomposition, we search for additional
    relevant agents based on the specific steps identified.

    Args:
        user_id: The user ID
        decomposition_result: Result from decompose_goal containing steps
        existing_agents: Already fetched library agents from initial search
        exclude_graph_id: Optional graph ID to exclude
        include_marketplace: Whether to also search marketplace
        max_additional_results: Max additional agents per search term (default 10)

    Returns:
        Combined list of library agents (existing + newly discovered)
    """
    search_terms = extract_search_terms_from_steps(decomposition_result)

    if not search_terms:
        return list(existing_agents)

    existing_ids: set[str] = set()
    existing_names: set[str] = set()

    for agent in existing_agents:
        agent_name = agent.get("name")
        if agent_name and isinstance(agent_name, str):
            existing_names.add(agent_name.lower())
        graph_id = agent.get("graph_id")  # type: ignore[call-overload]
        if graph_id and isinstance(graph_id, str):
            existing_ids.add(graph_id)

    all_agents: list[AgentSummary] | list[dict[str, Any]] = list(existing_agents)

    for term in search_terms[:3]:
        try:
            additional_agents = await get_all_relevant_agents_for_generation(
                user_id=user_id,
                search_query=term,
                exclude_graph_id=exclude_graph_id,
                include_marketplace=include_marketplace,
                max_library_results=max_additional_results,
                max_marketplace_results=5,
            )

            for agent in additional_agents:
                agent_name = agent.get("name")
                if not agent_name or not isinstance(agent_name, str):
                    continue
                agent_name_lower = agent_name.lower()

                if agent_name_lower in existing_names:
                    continue

                graph_id = agent.get("graph_id")  # type: ignore[call-overload]
                if graph_id and graph_id in existing_ids:
                    continue

                all_agents.append(agent)
                existing_names.add(agent_name_lower)
                if graph_id and isinstance(graph_id, str):
                    existing_ids.add(graph_id)

        except DatabaseError:
            logger.error(f"Database error searching for agents with term '{term}'")
            raise
        except Exception as e:
            logger.warning(
                f"Failed to search for additional agents with term '{term}': {e}"
            )

    logger.debug(
        f"Enriched library agents: {len(existing_agents)} initial + "
        f"{len(all_agents) - len(existing_agents)} additional = {len(all_agents)} total"
    )

    return all_agents