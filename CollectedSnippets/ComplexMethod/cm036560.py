def test_delimiter_preserved_fast_detokenization(self, parser):
        """DSML delimiters as literal text must still be detected."""
        # Delimiters appear as regular text (fast detokenization scenario).
        model_output = (
            f"{FC_START}\n"
            f'{INV_START}get_weather">\n'
            f'{PARAM_START}location" string="true">Tokyo{PARAM_END}\n'
            f"{INV_END}\n"
            f"{FC_END}"
        )

        # Non-streaming: parser must detect the tool call
        result = parser.extract_tool_calls(model_output, None)
        assert result.tools_called
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].function.name == "get_weather"
        assert json.loads(result.tool_calls[0].function.arguments) == {
            "location": "Tokyo"
        }

        assert result.content is None

        # With content prefix
        prefixed_output = "Here is the weather: " + model_output
        result2 = parser.extract_tool_calls(prefixed_output, None)
        assert result2.tools_called
        assert result2.content == "Here is the weather: "