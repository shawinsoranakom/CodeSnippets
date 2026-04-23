def test_tag_format_consistency(self, reasoning_parser):
        """Test that all generated tags follow consistent format,
        catching malformed tags from from_builtin_tool_to_tag."""
        tool_server = Mock(spec=ToolServer)
        tool_server.has_tool = Mock(
            side_effect=lambda tool: tool in ["python", "browser"]
        )

        result = reasoning_parser.prepare_structured_tag(None, tool_server)
        parsed_result = json.loads(result)

        for tag in parsed_result["format"]["tags"]:
            assert "begin" in tag
            assert "content" in tag
            assert "end" in tag
            assert tag["content"]["type"] == "any_text"
            assert tag["end"] == "<|end|>"
            assert tag["begin"].startswith("<|channel|>")