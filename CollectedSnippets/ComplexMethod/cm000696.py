async def test_orchestrator_handles_dynamic_dict_fields():
    """Test Orchestrator can handle dynamic dictionary fields (_#_) for any block"""

    # Create a mock node for CreateDictionaryBlock
    mock_node = Mock()
    mock_node.block = CreateDictionaryBlock()
    mock_node.block_id = CreateDictionaryBlock().id
    mock_node.input_default = {}
    mock_node.metadata = {}

    # Create mock links with dynamic dictionary fields
    mock_links = [
        Mock(
            source_name="tools_^_create_dict_~_name",
            sink_name="values_#_name",  # Dynamic dict field
            sink_id="dict_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_create_dict_~_age",
            sink_name="values_#_age",  # Dynamic dict field
            sink_id="dict_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_create_dict_~_city",
            sink_name="values_#_city",  # Dynamic dict field
            sink_id="dict_node_id",
            source_id="orchestrator_node_id",
        ),
    ]

    # Generate function signature
    signature = await OrchestratorBlock._create_block_function_signature(
        mock_node, mock_links  # type: ignore
    )

    # Verify the signature was created successfully
    assert signature["type"] == "function"
    assert "parameters" in signature["function"]
    assert "properties" in signature["function"]["parameters"]

    # Check that dynamic fields are handled with original names
    properties = signature["function"]["parameters"]["properties"]
    assert len(properties) == 3  # Should have all three fields

    # Check that field names are cleaned (for Anthropic API compatibility)
    assert "values___name" in properties
    assert "values___age" in properties
    assert "values___city" in properties

    # Each dynamic field should have proper schema with descriptive text
    for field_name, prop_value in properties.items():
        assert "type" in prop_value
        assert prop_value["type"] == "string"  # Dynamic fields get string type
        assert "description" in prop_value
        # Check that descriptions properly explain the dynamic field
        if field_name == "values___name":
            assert "Dictionary field 'name'" in prop_value["description"]
            assert "values['name']" in prop_value["description"]