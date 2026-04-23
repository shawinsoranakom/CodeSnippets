def test_create_multi_serve_app_multiple_flows(self, real_graph, mock_meta, simple_chat_json):
        """Test creating app with multiple flows."""
        # Create second real graph using from_payload
        graph2 = Graph.from_payload(simple_chat_json, flow_id="flow-2")

        meta2 = FlowMeta(
            id="flow-2",
            relative_path="flow2.json",
            title="Flow 2",
            description="Second flow",
        )

        graphs = {"test-flow-id": real_graph, "flow-2": graph2}
        metas = {"test-flow-id": mock_meta, "flow-2": meta2}
        verbose_print = Mock()

        app = create_multi_serve_app(
            root_dir=Path("/test"),
            graphs=graphs,
            metas=metas,
            verbose_print=verbose_print,
        )

        assert app.title == "LFX Multi-Flow Server (2)"
        assert "Use `/flows` to list available IDs" in app.description

        # Check routes
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/flows" in routes
        assert "/flows/test-flow-id/run" in routes
        assert "/flows/test-flow-id/info" in routes
        assert "/flows/flow-2/run" in routes
        assert "/flows/flow-2/info" in routes