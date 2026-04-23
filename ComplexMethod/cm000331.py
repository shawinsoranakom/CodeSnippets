async def create_test_library_agents(self) -> List[Dict[str, Any]]:
        """Create test library agents using the API function."""
        print("Creating test library agents...")

        library_agents = []
        for user in self.users:
            num_agents = random.randint(MIN_AGENTS_PER_USER, MAX_AGENTS_PER_USER)

            # Get available graphs for this user
            user_graphs = [
                g for g in self.agent_graphs if g.get("userId") == user["id"]
            ]
            if not user_graphs:
                continue

            # Shuffle and take unique graphs to avoid duplicates
            random.shuffle(user_graphs)
            selected_graphs = user_graphs[: min(num_agents, len(user_graphs))]

            for graph_data in selected_graphs:
                try:
                    # Get the graph model from the database
                    from backend.data.graph import get_graph

                    graph = await get_graph(
                        graph_data["id"],
                        graph_data.get("version", 1),
                        user_id=user["id"],
                    )
                    if graph:
                        # Use the API function to create library agent
                        library_agents.extend(
                            v.model_dump()
                            for v in await create_library_agent(graph, user["id"])
                        )
                except Exception as e:
                    print(f"Error creating library agent: {e}")
                    continue

        self.library_agents = library_agents
        return library_agents