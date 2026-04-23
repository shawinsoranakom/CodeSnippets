async def test_build_output_creates_valid_dataframe(self, component):
        """Test that build_output creates a valid DataFrame with mixed JSON types."""
        # Setup component with mocked tools and cache
        component.tool = "test_tool"
        component.tools = []

        # Mock the tool cache
        mock_tool = MagicMock()
        mock_result = MagicMock()

        # Create mock output with various JSON types
        mock_content_item1 = MagicMock()
        mock_content_item1.model_dump.return_value = {"type": "text", "text": '{"status": "success"}'}

        mock_content_item2 = MagicMock()
        mock_content_item2.model_dump.return_value = {"type": "text", "text": '"just a string"'}

        mock_content_item3 = MagicMock()
        mock_content_item3.model_dump.return_value = {"type": "text", "text": "42"}

        mock_result.content = [mock_content_item1, mock_content_item2, mock_content_item3]
        mock_tool.coroutine = AsyncMock(return_value=mock_result)

        component._tool_cache = {"test_tool": mock_tool}

        # Mock update_tool_list
        component.update_tool_list = AsyncMock(return_value=([], None))

        # Mock get_inputs_for_all_tools to return empty list
        component.get_inputs_for_all_tools = MagicMock(return_value={"test_tool": []})

        # Execute build_output
        result = await component.build_output()

        # Verify result is a DataFrame
        assert isinstance(result, DataFrame)

        # Verify all items in DataFrame are dictionaries
        for _idx, row in result.iterrows():
            # Each row should be a valid Series (which can be converted to dict)
            assert row is not None

        # Verify the DataFrame has the expected number of rows
        assert len(result) == 3

        # Verify first row is the original dict
        assert result.iloc[0]["status"] == "success"

        # Verify second row is wrapped string
        assert result.iloc[1]["parsed_value"] == "just a string"
        assert result.iloc[1]["type"] == "text"

        # Verify third row is wrapped number
        assert result.iloc[2]["parsed_value"] == 42
        assert result.iloc[2]["type"] == "text"