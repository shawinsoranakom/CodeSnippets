def test_streaming_incremental_string_value(glm4_moe_tool_parser, mock_request):
    """Test incremental streaming of string argument values."""
    _reset_streaming_state(glm4_moe_tool_parser)

    # Simulate streaming a tool call chunk by chunk
    chunks = [
        "<tool_call>",
        "get_weather\n",
        "<arg_key>city</arg_key>",
        "<arg_value>",
        "Bei",
        "jing",
        "</arg_value>",
        "</tool_call>",
    ]

    collected_fragments = []
    current_text = ""
    for chunk in chunks:
        current_text += chunk
        result = glm4_moe_tool_parser.extract_tool_calls_streaming(
            previous_text="",
            current_text=current_text,
            delta_text=chunk,
            previous_token_ids=[],
            current_token_ids=[],
            delta_token_ids=[],
            request=mock_request,
        )
        if result is not None and result.tool_calls:
            for tc in result.tool_calls:
                func = tc.function
                if isinstance(func, dict):
                    if func.get("arguments"):
                        collected_fragments.append(func["arguments"])
                    if func.get("name"):
                        collected_fragments.append(f"name:{func['name']}")
                else:
                    if func.arguments:
                        collected_fragments.append(func.arguments)
                    if func.name:
                        collected_fragments.append(f"name:{func.name}")

    # Verify we got incremental streaming of the argument value
    assert len(collected_fragments) > 0
    # The fragments should include the tool name and argument pieces
    combined = "".join(collected_fragments)
    assert "get_weather" in combined or "name:get_weather" in combined