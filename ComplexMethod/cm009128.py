def test_web_search(output_version: Literal["responses/v1", "v1"]) -> None:
    llm = ChatOpenAI(model=MODEL_NAME, output_version=output_version)
    first_response = llm.invoke(
        "What was a positive news story from today?",
        tools=[{"type": "web_search_preview"}],
    )
    _check_response(first_response)

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream(
        "What was a positive news story from today?",
        tools=[{"type": "web_search_preview"}],
    ):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    _check_response(full)

    # Use OpenAI's stateful API
    response = llm.invoke(
        "what about a negative one",
        tools=[{"type": "web_search_preview"}],
        previous_response_id=first_response.response_metadata["id"],
    )
    _check_response(response)

    # Manually pass in chat history
    response = llm.invoke(
        [
            {"role": "user", "content": "What was a positive news story from today?"},
            first_response,
            {"role": "user", "content": "what about a negative one"},
        ],
        tools=[{"type": "web_search_preview"}],
    )
    _check_response(response)

    # Bind tool
    response = llm.bind_tools([{"type": "web_search_preview"}]).invoke(
        "What was a positive news story from today?"
    )
    _check_response(response)

    for msg in [first_response, full, response]:
        assert msg is not None
        block_types = [block["type"] for block in msg.content]  # type: ignore[index]
        if output_version == "responses/v1":
            assert block_types == ["web_search_call", "text"]
        else:
            assert block_types == ["server_tool_call", "server_tool_result", "text"]