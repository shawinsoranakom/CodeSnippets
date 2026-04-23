async def get_library_agents_for_generation(
    user_id: str,
    search_query: str | None = None,
    exclude_graph_id: str | None = None,
    max_results: int = 15,
) -> list[LibraryAgentSummary]:
    """Fetch user's library agents formatted for Agent Generator.

    Uses search-based fetching to return relevant agents instead of all agents.
    This is more scalable for users with large libraries.

    Includes recent_executions list to help the LLM assess agent quality:
    - Each execution has status, correctness_score (0-1), and activity_summary
    - This gives the LLM concrete examples of recent performance

    Args:
        user_id: The user ID
        search_query: Optional search term to find relevant agents (user's goal/description)
        exclude_graph_id: Optional graph ID to exclude (prevents circular references)
        max_results: Maximum number of agents to return (default 15)

    Returns:
        List of LibraryAgentSummary with schemas and recent executions for sub-agent composition
    """
    search_term = search_query.strip() if search_query else None
    if search_term and len(search_term) > 100:
        raise ValueError(
            f"Search query is too long ({len(search_term)} chars, max 100). "
            f"Please use a shorter, more specific search term."
        )

    try:
        response = await library_db().list_library_agents(
            user_id=user_id,
            search_term=search_term,
            page=1,
            page_size=max_results,
            include_executions=True,
        )

        results: list[LibraryAgentSummary] = []
        for agent in response.agents:
            if exclude_graph_id is not None and agent.graph_id == exclude_graph_id:
                continue

            summary = LibraryAgentSummary(
                graph_id=agent.graph_id,
                graph_version=agent.graph_version,
                name=agent.name,
                description=agent.description,
                input_schema=agent.input_schema,
                output_schema=agent.output_schema,
            )
            if agent.recent_executions:
                exec_summaries: list[ExecutionSummary] = []
                for ex in agent.recent_executions:
                    exec_sum = ExecutionSummary(status=ex.status)
                    if ex.correctness_score is not None:
                        exec_sum["correctness_score"] = ex.correctness_score
                    if ex.activity_summary:
                        exec_sum["activity_summary"] = ex.activity_summary
                    exec_summaries.append(exec_sum)
                summary["recent_executions"] = exec_summaries
            results.append(summary)
        return results
    except DatabaseError:
        raise
    except Exception as e:
        logger.warning(f"Failed to fetch library agents: {e}")
        return []