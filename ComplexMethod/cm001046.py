async def _resolve_agent(
        self,
        user_id: str,
        agent_name: str | None,
        library_agent_id: str | None,
        store_slug: str | None,
    ) -> tuple[LibraryAgent | None, str | None]:
        """
        Resolve agent from provided identifiers.
        Returns (library_agent, error_message).
        """
        lib_db = library_db()

        # Priority 1: Exact library agent ID
        if library_agent_id:
            try:
                agent = await lib_db.get_library_agent(library_agent_id, user_id)
                return agent, None
            except Exception as e:
                logger.warning(f"Failed to get library agent by ID: {e}")
                return None, f"Library agent '{library_agent_id}' not found"

        # Priority 2: Store slug (username/agent-name)
        if store_slug and "/" in store_slug:
            username, agent_slug = store_slug.split("/", 1)
            graph, _ = await fetch_graph_from_store_slug(username, agent_slug)
            if not graph:
                return None, f"Agent '{store_slug}' not found in marketplace"

            # Find in user's library by graph_id
            agent = await lib_db.get_library_agent_by_graph_id(user_id, graph.id)
            if not agent:
                return (
                    None,
                    f"Agent '{store_slug}' is not in your library. "
                    "Add it first to see outputs.",
                )
            return agent, None

        # Priority 3: Fuzzy name search in library
        if agent_name:
            try:
                response = await lib_db.list_library_agents(
                    user_id=user_id,
                    search_term=agent_name,
                    page_size=5,
                )
                if not response.agents:
                    return (
                        None,
                        f"No agents matching '{agent_name}' found in your library",
                    )

                # Return best match (first result from search)
                return response.agents[0], None
            except Exception as e:
                logger.error(f"Error searching library agents: {e}")
                return None, f"Error searching for agent: {e}"

        return (
            None,
            "Please specify an agent name, library_agent_id, or store_slug",
        )