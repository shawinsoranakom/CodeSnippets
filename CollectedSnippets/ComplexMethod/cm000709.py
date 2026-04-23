async def test_create_block_function_signature_with_dict_fields():
    """Test that function signatures are created correctly for dictionary dynamic fields."""
    block = OrchestratorBlock()

    # Create a mock node for CreateDictionaryBlock
    mock_node = Mock()
    mock_node.block = CreateDictionaryBlock()
    mock_node.block_id = CreateDictionaryBlock().id
    mock_node.input_default = {}
    mock_node.metadata = {}

    # Create mock links with dynamic dictionary fields (source sanitized, sink original)
    mock_links = [
        Mock(
            source_name="tools_^_create_dict_~_values___name",  # Sanitized source
            sink_name="values_#_name",  # Original sink
            sink_id="dict_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_create_dict_~_values___age",  # Sanitized source
            sink_name="values_#_age",  # Original sink
            sink_id="dict_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_create_dict_~_values___email",  # Sanitized source
            sink_name="values_#_email",  # Original sink
            sink_id="dict_node_id",
            source_id="orchestrator_node_id",
        ),
    ]

    # Generate function signature
    signature = await block._create_block_function_signature(mock_node, mock_links)  # type: ignore

    # Verify the signature structure
    assert signature["type"] == "function"
    assert "function" in signature
    assert "parameters" in signature["function"]
    assert "properties" in signature["function"]["parameters"]

    # Check that dynamic fields are handled with original names
    properties = signature["function"]["parameters"]["properties"]
    assert len(properties) == 3

    # Check cleaned field names (for Anthropic API compatibility)
    assert "values___name" in properties
    assert "values___age" in properties
    assert "values___email" in properties

    # Check descriptions mention they are dictionary fields
    assert "Dictionary field" in properties["values___name"]["description"]
    assert "values['name']" in properties["values___name"]["description"]

    assert "Dictionary field" in properties["values___age"]["description"]
    assert "values['age']" in properties["values___age"]["description"]

    assert "Dictionary field" in properties["values___email"]["description"]
    assert "values['email']" in properties["values___email"]["description"]