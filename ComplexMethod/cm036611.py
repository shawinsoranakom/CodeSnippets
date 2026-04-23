def test_streaming_mtp_variable_chunks(
    step3p5_tool_parser, step3p5_tokenizer, sample_tools
):
    """Regression: MTP variable-size chunks spanning param boundaries (PR #33690)."""
    request = ChatCompletionRequest(model=MODEL, messages=[], tools=sample_tools)

    delta_text_chunks = [
        "<tool_call>\n<function=get_current_weather>\n<parameter=city>\n",
        "Dallas\n</parameter>\n<parameter=state>\nTX",
        "\n</parameter>\n<parameter=unit>\nfahrenheit\n</parameter>",
        "\n</function>\n</tool_call>",
    ]

    _, tool_states = _accumulate_tool_states(
        stream_delta_message_generator_from_chunks(
            step3p5_tool_parser, step3p5_tokenizer, delta_text_chunks, request
        )
    )

    assert len(tool_states) == 1

    state = tool_states[0]
    assert state["id"] is not None
    assert state["type"] == "function"
    assert state["name"] == "get_current_weather"

    args = json.loads(state["arguments"])
    assert args["city"] == "Dallas"
    assert args["state"] == "TX"
    assert args["unit"] == "fahrenheit"