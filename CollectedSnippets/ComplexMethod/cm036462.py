def test_json_validity_comprehensive(self, reasoning_parser, tools):
        """Test JSON validity across all possible tool combinations."""
        tool_server = Mock(spec=ToolServer)
        tool_server.has_tool = Mock(side_effect=lambda tool: tool in tools)

        result = reasoning_parser.prepare_structured_tag(None, tool_server)
        parsed_result = json.loads(result)

        assert parsed_result["type"] == "structural_tag"
        assert "format" in parsed_result
        assert "tags" in parsed_result["format"]
        assert "triggers" in parsed_result["format"]

        # Tag count should be: 1 (analysis) + 2 * len(tools)
        expected_tag_count = 1 + (2 * len(tools))
        assert len(parsed_result["format"]["tags"]) == expected_tag_count

        # Verify triggers are correctly configured
        expected_triggers = ["<|channel|>analysis"]
        if tools:
            expected_triggers.append("<|channel|>commentary to=")
        assert set(parsed_result["format"]["triggers"]) == set(expected_triggers)