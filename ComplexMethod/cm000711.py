async def test_create_tool_node_signatures():
    """Test that the mapping between sanitized and original field names is built correctly."""
    block = OrchestratorBlock()

    # Mock the database client and connected nodes
    with patch(
        "backend.blocks.orchestrator.get_database_manager_async_client"
    ) as mock_db:
        mock_client = AsyncMock()
        mock_db.return_value = mock_client

        # Create mock nodes and links
        mock_dict_node = Mock()
        mock_dict_node.block = CreateDictionaryBlock()
        mock_dict_node.block_id = CreateDictionaryBlock().id
        mock_dict_node.input_default = {}
        mock_dict_node.metadata = {}

        mock_list_node = Mock()
        mock_list_node.block = AddToListBlock()
        mock_list_node.block_id = AddToListBlock().id
        mock_list_node.input_default = {}
        mock_list_node.metadata = {}

        # Mock links with dynamic fields
        dict_link1 = Mock(
            source_name="tools_^_create_dictionary_~_name",
            sink_name="values_#_name",
            sink_id="dict_node_id",
            source_id="test_node_id",
        )
        dict_link2 = Mock(
            source_name="tools_^_create_dictionary_~_age",
            sink_name="values_#_age",
            sink_id="dict_node_id",
            source_id="test_node_id",
        )
        list_link = Mock(
            source_name="tools_^_add_to_list_~_0",
            sink_name="entries_$_0",
            sink_id="list_node_id",
            source_id="test_node_id",
        )

        mock_client.get_connected_output_nodes.return_value = [
            (dict_link1, mock_dict_node),
            (dict_link2, mock_dict_node),
            (list_link, mock_list_node),
        ]

        # Call the method that builds signatures
        tool_functions = await block._create_tool_node_signatures("test_node_id")

        # Verify we got 2 tool functions (one for dict, one for list)
        assert len(tool_functions) == 2

        # Verify the tool functions contain the dynamic field names
        dict_tool = next(
            (
                tool
                for tool in tool_functions
                if tool["function"]["name"] == "createdictionaryblock"
            ),
            None,
        )
        assert dict_tool is not None
        dict_properties = dict_tool["function"]["parameters"]["properties"]
        assert "values___name" in dict_properties
        assert "values___age" in dict_properties

        list_tool = next(
            (
                tool
                for tool in tool_functions
                if tool["function"]["name"] == "addtolistblock"
            ),
            None,
        )
        assert list_tool is not None
        list_properties = list_tool["function"]["parameters"]["properties"]
        assert "entries___0" in list_properties