def test_multiple_tool_calls(self, parser):
        """Two tool calls emitted with correct indices, names, arguments."""
        deltas = _split_tool_output_to_deltas(
            "Compare weather. ",
            [
                ("functions.get_weather:0", '{"city": "Tokyo"}'),
                ("functions.get_weather:1", '{"city": "NYC"}'),
            ],
        )
        rec = run_tool_extraction_streaming(parser, deltas)

        assert len(rec.tool_calls) == 2
        assert rec.tool_calls[0].function.name == "get_weather"
        assert rec.tool_calls[0].id == "functions.get_weather:0"
        assert json.loads(rec.tool_calls[0].function.arguments) == {"city": "Tokyo"}

        assert rec.tool_calls[1].function.name == "get_weather"
        assert rec.tool_calls[1].id == "functions.get_weather:1"
        assert json.loads(rec.tool_calls[1].function.arguments) == {"city": "NYC"}