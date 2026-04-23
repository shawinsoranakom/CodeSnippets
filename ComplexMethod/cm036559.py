def test_streaming_matches_non_streaming(self, parser):
        """Streaming and non-streaming must produce the same result."""
        full_text = build_tool_call(
            "get_weather", {"location": "SF", "date": "2024-01-16"}
        )
        # Non-streaming
        non_stream = parser.extract_tool_calls(full_text, None)
        assert non_stream.tools_called
        ns_name = non_stream.tool_calls[0].function.name
        ns_args = json.loads(non_stream.tool_calls[0].function.arguments)
        # Streaming
        deltas = self._stream(parser, full_text)
        s_names = [
            tc.function.name
            for d in deltas
            if d.tool_calls
            for tc in d.tool_calls
            if tc.function and tc.function.name
        ]
        s_args = json.loads(self._reconstruct_args(deltas))
        assert s_names[0] == ns_name
        assert s_args == ns_args