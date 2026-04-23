async def test_turn_prefix_contains_version_nodes_and_links():
    session = _session("graph-1")
    nodes = [
        {
            "id": "n1",
            "block_id": "block-A",
            "input_default": {"name": "Input"},
            "metadata": {},
        },
        {
            "id": "n2",
            "block_id": "block-B",
            "input_default": {},
            "metadata": {},
        },
    ]
    links = [
        {
            "source_id": "n1",
            "sink_id": "n2",
            "source_name": "out",
            "sink_name": "in",
        }
    ]
    agent = _agent_json(nodes=nodes, links=links)
    with patch(
        "backend.copilot.builder_context.get_agent_as_json",
        new=AsyncMock(return_value=agent),
    ):
        block = await build_builder_context_turn_prefix(session, "user-1")

    assert block.startswith(f"<{BUILDER_CONTEXT_TAG}>\n")
    assert block.endswith(f"</{BUILDER_CONTEXT_TAG}>\n\n")
    assert 'id="graph-1"' in block
    assert 'name="My Agent"' in block
    assert 'version="3"' in block
    assert 'node_count="2"' in block
    assert 'edge_count="1"' in block
    assert "n1: Input (block-A)" in block
    assert "n2: block-B (block-B)" in block
    assert "Input.out -> block-B.in" in block