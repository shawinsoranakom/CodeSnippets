async def test_orchestrator_handles_dynamic_list_fields():
    """Test Orchestrator can handle dynamic list fields (_$_) for any block"""

    # Create a mock node for AddToListBlock
    mock_node = Mock()
    mock_node.block = AddToListBlock()
    mock_node.block_id = AddToListBlock().id
    mock_node.input_default = {}
    mock_node.metadata = {}

    # Create mock links with dynamic list fields
    mock_links = [
        Mock(
            source_name="tools_^_add_to_list_~_0",
            sink_name="entries_$_0",  # Dynamic list field
            sink_id="list_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_add_to_list_~_1",
            sink_name="entries_$_1",  # Dynamic list field
            sink_id="list_node_id",
            source_id="orchestrator_node_id",
        ),
    ]

    # Generate function signature
    signature = await OrchestratorBlock._create_block_function_signature(
        mock_node, mock_links  # type: ignore
    )

    # Verify dynamic list fields are handled properly
    assert signature["type"] == "function"
    properties = signature["function"]["parameters"]["properties"]
    assert len(properties) == 2  # Should have both list items

    # Check that field names are cleaned (for Anthropic API compatibility)
    assert "entries___0" in properties
    assert "entries___1" in properties

    # Each dynamic field should have proper schema with descriptive text
    for field_name, prop_value in properties.items():
        assert prop_value["type"] == "string"
        assert "description" in prop_value
        # Check that descriptions properly explain the list field
        if field_name == "entries___0":
            assert "List item 0" in prop_value["description"]
            assert "entries[0]" in prop_value["description"]