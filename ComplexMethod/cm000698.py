async def test_duplicate_tools_include_defaults_in_description():
    """Duplicate tools should have hardcoded defaults in description."""
    block = MatchTextPatternBlock()
    node_a = _make_mock_node(
        block, "node_a", input_default={"match": "error", "case_sensitive": True}
    )
    node_b = _make_mock_node(
        block, "node_b", input_default={"match": "warning", "case_sensitive": False}
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

    # Find each tool by suffix
    tool_1 = next(t for t in tools if t["function"]["name"].endswith("_1"))
    tool_2 = next(t for t in tools if t["function"]["name"].endswith("_2"))

    # Descriptions should contain the hardcoded defaults (not the linked 'text' field)
    assert "[Pre-configured:" in tool_1["function"]["description"]
    assert "[Pre-configured:" in tool_2["function"]["description"]
    assert '"error"' in tool_1["function"]["description"]
    assert '"warning"' in tool_2["function"]["description"]