def test_from_builtin_tool_to_tag(self):
        """Test from_builtin_tool_to_tag function."""
        tags = from_builtin_tool_to_tag("python")

        assert len(tags) == 2
        assert tags[0]["begin"] == "<|channel|>commentary to=python"
        assert tags[0]["content"]["type"] == "any_text"
        assert tags[0]["end"] == "<|end|>"

        assert tags[1]["begin"] == "<|channel|>analysis to=python"
        assert tags[1]["content"]["type"] == "any_text"
        assert tags[1]["end"] == "<|end|>"