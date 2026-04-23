async def test_very_long_block_names_truncated_with_suffix():
    """Block names > 64 chars must be truncated so name+suffix fits in 64 chars."""
    block = MatchTextPatternBlock()
    # A name that is exactly 70 characters long
    long_name = "x" * 70

    node_a = _make_mock_node(block, "node_a", metadata={"customized_name": long_name})
    node_b = _make_mock_node(block, "node_b", metadata={"customized_name": long_name})

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

    names = [t["function"]["name"] for t in tools]
    assert len(names) == 2
    assert len(set(names)) == 2, f"Tool names are not unique: {names}"
    for name in names:
        assert len(name) <= 64, f"Tool name exceeds 64 chars: {name!r} ({len(name)})"
    # Suffixes should still be present
    assert any(n.endswith("_1") for n in names)
    assert any(n.endswith("_2") for n in names)