async def test_three_duplicates_all_get_unique_names():
    """Three nodes with same block type should all get unique suffixed names."""
    block = MatchTextPatternBlock()
    nodes_and_links = []
    for i, pattern in enumerate(["error", "warning", "info"]):
        node = _make_mock_node(block, f"node_{i}", input_default={"match": pattern})
        link = _make_mock_link(f"tools_^_{i}_~_text", "text", f"node_{i}", "orch")
        nodes_and_links.append((link, node))

    mock_db = AsyncMock()
    mock_db.get_connected_output_nodes.return_value = nodes_and_links

    with patch(
        "backend.blocks.orchestrator.get_database_manager_async_client",
        return_value=mock_db,
    ):
        tools = await OrchestratorBlock._create_tool_node_signatures("orch")

    names = [t["function"]["name"] for t in tools]
    assert len(names) == 3
    assert len(set(names)) == 3, f"Tool names are not unique: {names}"
    base = OrchestratorBlock.cleanup(block.name)
    assert f"{base}_1" in names
    assert f"{base}_2" in names
    assert f"{base}_3" in names