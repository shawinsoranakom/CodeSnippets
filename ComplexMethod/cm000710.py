async def test_create_block_function_signature_with_list_fields():
    """Test that function signatures are created correctly for list dynamic fields."""
    block = OrchestratorBlock()

    # Create a mock node for AddToListBlock
    mock_node = Mock()
    mock_node.block = AddToListBlock()
    mock_node.block_id = AddToListBlock().id
    mock_node.input_default = {}
    mock_node.metadata = {}

    # Create mock links with dynamic list fields
    mock_links = [
        Mock(
            source_name="tools_^_add_list_~_0",
            sink_name="entries_$_0",  # Dynamic list field
            sink_id="list_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_add_list_~_1",
            sink_name="entries_$_1",  # Dynamic list field
            sink_id="list_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_add_list_~_2",
            sink_name="entries_$_2",  # Dynamic list field
            sink_id="list_node_id",
            source_id="orchestrator_node_id",
        ),
    ]

    # Generate function signature
    signature = await block._create_block_function_signature(mock_node, mock_links)  # type: ignore

    # Verify the signature structure
    assert signature["type"] == "function"
    properties = signature["function"]["parameters"]["properties"]

    # Check cleaned field names (for Anthropic API compatibility)
    assert "entries___0" in properties
    assert "entries___1" in properties
    assert "entries___2" in properties

    # Check descriptions mention they are list items
    assert "List item 0" in properties["entries___0"]["description"]
    assert "entries[0]" in properties["entries___0"]["description"]

    assert "List item 1" in properties["entries___1"]["description"]
    assert "entries[1]" in properties["entries___1"]["description"]