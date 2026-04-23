async def test_cache_enabled_reuses_graph_with_real_flow(self, client, logged_in_headers, active_user):
        """Test that with cache_flow=True, the graph is cached and reused with a real flow."""
        # Create a REAL flow in the database
        text_input = TextInputComponent()
        text_output = TextOutputComponent()
        graph = Graph(start=text_input, end=text_output)
        graph_dict = graph.dump(name="Cached Flow", description="Flow to test caching")
        flow = FlowCreate(**graph_dict)

        # Create flow via API
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201
        flow_data = response.json()
        flow_id = flow_data["id"]
        flow_name = flow_data["name"]

        try:
            # Setup component with caching ENABLED
            component = RunFlowComponent()
            component._user_id = str(active_user.id)
            component._flow_id = str(uuid4())
            component.cache_flow = True  # Caching enabled

            # First access - should fetch from database
            graph1 = await component.get_graph(flow_name_selected=flow_name, flow_id_selected=flow_id)

            # Verify it's a real graph
            assert graph1 is not None
            assert graph1.flow_name == flow_name
            assert len(graph1.vertices) > 0

            # Second access - should reuse cached graph (same instance)
            graph2 = await component.get_graph(flow_name_selected=flow_name, flow_id_selected=flow_id)

            # With caching, should return the same graph instance
            assert graph2 is not None
            assert graph2.flow_name == flow_name
            assert graph1 == graph2, "Expected same graph instance from cache"
        finally:
            # Cleanup
            await client.delete(f"api/v1/flows/{flow_id}", headers=logged_in_headers)