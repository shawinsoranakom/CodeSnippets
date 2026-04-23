def test_unicode_characters_preserved(glm4_moe_tool_parser, mock_request):
    """Regression: Unicode chars must not be escaped to \\uXXXX (PR #30920)."""
    model_output = """<tool_call>send_message
<arg_key>greeting</arg_key>
<arg_value>你好世界</arg_value>
<arg_key>emoji</arg_key>
<arg_value>🎉</arg_value>
</tool_call>"""

    extracted = glm4_moe_tool_parser.extract_tool_calls(
        model_output, request=mock_request
    )  # type: ignore[arg-type]

    assert extracted.tools_called
    assert len(extracted.tool_calls) == 1

    raw_args = extracted.tool_calls[0].function.arguments
    assert "你好世界" in raw_args
    assert "🎉" in raw_args
    assert "\\u4f60" not in raw_args
    parsed_args = json.loads(raw_args)
    assert parsed_args["greeting"] == "你好世界"
    assert parsed_args["emoji"] == "🎉"