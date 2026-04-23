async def test_mixed_regular_and_dynamic_fields():
    """Test handling of blocks with both regular and dynamic fields."""
    block = OrchestratorBlock()

    # Create a mock node
    mock_node = Mock()
    mock_node.block = Mock()
    mock_node.block.name = "TestBlock"
    mock_node.block.description = "A test block"
    mock_node.block.input_schema = Mock()
    mock_node.metadata = {}

    # Mock the get_field_schema to return a proper schema for regular fields
    def get_field_schema(field_name):
        if field_name == "regular_field":
            return {"type": "string", "description": "A regular field"}
        elif field_name == "values":
            return {"type": "object", "description": "A dictionary field"}
        else:
            raise KeyError(f"Field {field_name} not found")

    mock_node.block.input_schema.get_field_schema = get_field_schema
    mock_node.block.input_schema.jsonschema = Mock(
        return_value={"properties": {}, "required": []}
    )

    # Create links with both regular and dynamic fields
    mock_links = [
        Mock(
            source_name="tools_^_test_~_regular",
            sink_name="regular_field",  # Regular field
            sink_id="test_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_test_~_dict_key",
            sink_name="values_#_key1",  # Dynamic dict field
            sink_id="test_node_id",
            source_id="orchestrator_node_id",
        ),
        Mock(
            source_name="tools_^_test_~_dict_key2",
            sink_name="values_#_key2",  # Dynamic dict field
            sink_id="test_node_id",
            source_id="orchestrator_node_id",
        ),
    ]

    # Generate function signature
    signature = await block._create_block_function_signature(mock_node, mock_links)  # type: ignore

    # Check properties
    properties = signature["function"]["parameters"]["properties"]
    assert len(properties) == 3

    # Regular field should have its original schema
    assert "regular_field" in properties
    assert properties["regular_field"]["description"] == "A regular field"

    # Dynamic fields should have generated descriptions
    assert "values___key1" in properties
    assert "Dictionary field" in properties["values___key1"]["description"]

    assert "values___key2" in properties
    assert "Dictionary field" in properties["values___key2"]["description"]