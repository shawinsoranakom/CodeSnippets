async def test_truncation_surfaces_in_response(self):
        """When >_MAX_GRAPH_FETCHES agents have graphs, the response contains a truncation notice."""
        from backend.copilot.tools.agent_search import _MAX_GRAPH_FETCHES
        from backend.data.graph import BaseGraph

        agent_count = _MAX_GRAPH_FETCHES + 5
        mock_agents = []
        for i in range(agent_count):
            uid = f"a1b2c3d4-e5f6-4a7b-8c9d-{i:012d}"
            mock_agents.append(self._make_mock_library_agent(uid, uid))

        mock_lib_db = MagicMock()
        mock_search_results = MagicMock()
        mock_search_results.agents = mock_agents
        mock_lib_db.list_library_agents = AsyncMock(return_value=mock_search_results)

        fake_graph = BaseGraph(id="x", name="g", description="d")
        mock_gdb = MagicMock()
        mock_gdb.get_graph = AsyncMock(return_value=fake_graph)

        with (
            patch(
                "backend.copilot.tools.agent_search.library_db",
                return_value=mock_lib_db,
            ),
            patch(
                "backend.copilot.tools.agent_search.graph_db",
                return_value=mock_gdb,
            ),
        ):
            response = await search_agents(
                query="",
                source="library",
                session_id="s",
                user_id=_TEST_USER_ID,
                include_graph=True,
            )

        assert isinstance(response, AgentsFoundResponse)
        assert mock_gdb.get_graph.await_count == _MAX_GRAPH_FETCHES
        enriched = [a for a in response.agents if a.graph is not None]
        assert len(enriched) == _MAX_GRAPH_FETCHES
        assert "Graph data included for" in response.message
        assert str(_MAX_GRAPH_FETCHES) in response.message