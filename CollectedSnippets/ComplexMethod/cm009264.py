def test_tags_only_last_tool_with_cache_control(self) -> None:
        @tool
        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return "sunny"

        @tool
        def get_time(timezone: str) -> str:
            """Get time in a timezone."""
            return "12:00"

        result = self._run(self._make_request(tools=[get_weather, get_time]))
        assert result.tools is not None
        assert len(result.tools) == 2
        first = result.tools[0]
        assert isinstance(first, BaseTool)
        assert first.extras is None or "cache_control" not in first.extras
        last = result.tools[1]
        assert isinstance(last, BaseTool)
        assert last.extras is not None
        assert last.extras["cache_control"] == {"type": "ephemeral", "ttl": "5m"}