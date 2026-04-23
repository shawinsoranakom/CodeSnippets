async def test_suffixed_tool_call_routes_to_correct_node():
    """Round-trip: LLM calls a suffixed tool name and it routes to the right node.

    This verifies the reverse path of disambiguation.  After
    ``_create_tool_node_signatures`` produces suffixed names (_1, _2),
    ``_process_tool_calls`` must map the suffixed name back to the correct
    tool definition (and therefore the correct ``_sink_node_id``).

    Steps:
      1. Build two duplicate tools via ``_create_tool_node_signatures``.
      2. Simulate an LLM response that calls ``<base_name>_1``.
      3. Run ``_process_tool_calls`` and verify the resolved tool_def
         contains ``_sink_node_id == "node_a"`` (not "node_b").
    """
    block = MatchTextPatternBlock()
    node_a = _make_mock_node(block, "node_a", input_default={"match": "foo"})
    node_b = _make_mock_node(block, "node_b", input_default={"match": "bar"})

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
        tool_functions = await OrchestratorBlock._create_tool_node_signatures("orch")

    # Determine the suffixed names and their associated node IDs.
    base = OrchestratorBlock.cleanup(block.name)
    name_1 = f"{base}_1"
    name_2 = f"{base}_2"

    # Sanity: both suffixed names must exist.
    names = [t["function"]["name"] for t in tool_functions]
    assert name_1 in names
    assert name_2 in names

    # Build the node-id lookup the same way _process_tool_calls will use.
    tool_1_def = next(t for t in tool_functions if t["function"]["name"] == name_1)
    tool_2_def = next(t for t in tool_functions if t["function"]["name"] == name_2)

    # Simulate an LLM response calling name_1 with some arguments.
    mock_tool_call = SimpleNamespace(
        id="call_abc123",
        function=SimpleNamespace(
            name=name_1,
            arguments='{"text": "hello world"}',
        ),
    )
    mock_response = SimpleNamespace(tool_calls=[mock_tool_call])

    orchestrator = OrchestratorBlock()
    processed = orchestrator._process_tool_calls(mock_response, tool_functions)

    # Exactly one tool call was processed.
    assert len(processed) == 1
    result = processed[0]

    # The resolved tool_def must point to the FIRST node ("node_a"),
    # not the second ("node_b").
    assert result.tool_name == name_1
    assert (
        result.tool_def["function"]["_sink_node_id"]
        == tool_1_def["function"]["_sink_node_id"]
    )
    assert (
        result.tool_def["function"]["_sink_node_id"]
        != tool_2_def["function"]["_sink_node_id"]
    )

    # Verify the input data was correctly extracted via the field mapping.
    assert "text" in result.input_data

    # Now do the same for name_2 to confirm it routes to node_b.
    mock_tool_call_2 = SimpleNamespace(
        id="call_def456",
        function=SimpleNamespace(
            name=name_2,
            arguments='{"text": "goodbye world"}',
        ),
    )
    mock_response_2 = SimpleNamespace(tool_calls=[mock_tool_call_2])

    processed_2 = orchestrator._process_tool_calls(mock_response_2, tool_functions)
    assert len(processed_2) == 1
    result_2 = processed_2[0]

    assert result_2.tool_name == name_2
    assert (
        result_2.tool_def["function"]["_sink_node_id"]
        == tool_2_def["function"]["_sink_node_id"]
    )
    assert (
        result_2.tool_def["function"]["_sink_node_id"]
        != tool_1_def["function"]["_sink_node_id"]
    )