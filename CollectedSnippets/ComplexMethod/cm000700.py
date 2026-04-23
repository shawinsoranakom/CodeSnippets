async def test_sensitive_fields_excluded_from_defaults():
    """Credentials and other sensitive fields must not leak into descriptions."""
    block = MatchTextPatternBlock()
    node_a = _make_mock_node(
        block,
        "node_a",
        input_default={
            "match": "error",
            "credentials": {"api_key": "sk-secret"},
            "api_key": "my-key",
            "password": "hunter2",
        },
    )
    node_b = _make_mock_node(
        block, "node_b", input_default={"match": "warning", "credentials": {"x": "y"}}
    )

    link_a = _make_mock_link("tools_^_a_~_text", "text", "node_a", "orch")
    link_b = _make_mock_link("tools_^_b_~_text", "text", "node_b", "orch")

    mock_db = AsyncMock()
    mock_db.get_connected_output_nodes.return_value = [
        (link_a, node_a),
        (link_b, node_b),
    ]

    with patch(
        "backend.blocks.orchestrator.get_database_manager_async_client",
        return_value=mock_db,
    ):
        tools = await OrchestratorBlock._create_tool_node_signatures("orch")

    for tool in tools:
        desc = tool["function"].get("description", "")
        assert "sk-secret" not in desc
        assert "my-key" not in desc
        assert "hunter2" not in desc
        assert "credentials=" not in desc
        assert "api_key=" not in desc
        assert "password=" not in desc