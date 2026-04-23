def test_create_multi_serve_app_multiple_flows(mock_graph, test_flow_meta):
    """Test creating app for multiple flows."""
    meta2 = FlowMeta(
        id="flow-2",
        relative_path="flow2.json",
        title="Flow 2",
        description="Second flow",
    )

    with patch.dict(os.environ, {"LANGFLOW_API_KEY": "test-key"}):  # pragma: allowlist secret
        app = create_multi_serve_app(
            root_dir=Path("/tmp"),
            graphs={"test-flow-id": mock_graph, "flow-2": mock_graph},
            metas={"test-flow-id": test_flow_meta, "flow-2": meta2},
            verbose_print=lambda x: None,  # noqa: ARG005
        )

        client = TestClient(app)

        # Test flows listing
        response = client.get("/flows")
        assert response.status_code == 200
        flows = response.json()
        assert len(flows) == 2
        assert any(f["id"] == "test-flow-id" for f in flows)
        assert any(f["id"] == "flow-2" for f in flows)

        # Test individual flow run
        response = client.post(
            "/flows/test-flow-id/run",
            json={"input_value": "test"},
            headers={"x-api-key": "test-key"},
        )
        assert response.status_code == 200

        # Test flow info
        response = client.get(
            "/flows/test-flow-id/info",
            headers={"x-api-key": "test-key"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == "test-flow-id"