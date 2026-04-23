def test_phase_streaming(output_version: str) -> None:
    def get_weather(location: str) -> str:
        """Get the weather at a location."""
        return "It's sunny."

    model = ChatOpenAI(
        model="gpt-5.4",
        use_responses_api=True,
        verbosity="high",
        reasoning={"effort": "medium", "summary": "auto"},
        streaming=True,
        output_version=output_version,
    )

    agent = create_agent(model, tools=[get_weather])

    input_message = {
        "role": "user",
        "content": (
            "What's the weather in the oldest major city in the US? State your answer "
            "and then generate a tool call this turn."
        ),
    }
    result = agent.invoke({"messages": [input_message]})
    first_response = result["messages"][1]
    if output_version == "responses/v1":
        assert [block["type"] for block in first_response.content] == [
            "reasoning",
            "text",
            "function_call",
        ]
    else:
        assert [block["type"] for block in first_response.content] == [
            "reasoning",
            "text",
            "tool_call",
        ]
    text_block = next(
        block for block in first_response.content if block["type"] == "text"
    )
    assert text_block["phase"] == "commentary"

    final_response = result["messages"][-1]
    assert [block["type"] for block in final_response.content] == ["text"]
    text_block = next(
        block for block in final_response.content if block["type"] == "text"
    )
    assert text_block["phase"] == "final_answer"