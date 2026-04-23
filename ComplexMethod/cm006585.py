def test_validate_different_content_types(self):
        """Test ContentBlock with different content types."""
        contents = [
            TextContent(type="text", text="Sample text"),
            CodeContent(type="code", code="print('hello')", language="python"),
            ErrorContent(type="error", error="Sample error"),
            JSONContent(type="json", data={"key": "value"}),
            MediaContent(type="media", urls=["http://example.com/image.jpg"]),
            ToolContent(type="tool_use", output="Sample thought", name="test_tool", tool_input={"input": "test"}),
        ]

        content_block = ContentBlock(title="Test", contents=contents)
        expected_len = 6
        assert len(content_block.contents) == expected_len
        assert isinstance(content_block.contents[0], TextContent)
        assert isinstance(content_block.contents[1], CodeContent)
        assert isinstance(content_block.contents[2], ErrorContent)
        assert isinstance(content_block.contents[3], JSONContent)
        assert isinstance(content_block.contents[4], MediaContent)
        assert isinstance(content_block.contents[5], ToolContent)