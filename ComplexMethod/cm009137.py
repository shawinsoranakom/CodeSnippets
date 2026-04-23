def test_file_search(
    output_version: Literal["responses/v1", "v1"],
) -> None:
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    if not vector_store_id:
        pytest.skip()

    llm = ChatOpenAI(
        model=MODEL_NAME,
        use_responses_api=True,
        output_version=output_version,
    )
    tool = {
        "type": "file_search",
        "vector_store_ids": [vector_store_id],
    }

    input_message = {"role": "user", "content": "What is deep research by OpenAI?"}
    response = llm.invoke([input_message], tools=[tool])
    _check_response(response)

    if output_version == "v1":
        assert [block["type"] for block in response.content] == [  # type: ignore[index]
            "server_tool_call",
            "server_tool_result",
            "text",
        ]
    else:
        assert [block["type"] for block in response.content] == [  # type: ignore[index]
            "file_search_call",
            "text",
        ]

    full: AIMessageChunk | None = None
    for chunk in llm.stream([input_message], tools=[tool]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    _check_response(full)

    if output_version == "v1":
        assert [block["type"] for block in full.content] == [  # type: ignore[index]
            "server_tool_call",
            "server_tool_result",
            "text",
        ]
    else:
        assert [block["type"] for block in full.content] == ["file_search_call", "text"]  # type: ignore[index]

    next_message = {"role": "user", "content": "Thank you."}
    _ = llm.invoke([input_message, full, next_message])

    for message in [response, full]:
        assert [block["type"] for block in message.content_blocks] == [
            "server_tool_call",
            "server_tool_result",
            "text",
        ]