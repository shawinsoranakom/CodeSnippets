def test_web_fetch_v1(output_version: Literal["v0", "v1"]) -> None:
    """Test that http calls are unchanged between v0 and v1."""
    llm = ChatAnthropic(
        model=MODEL_NAME,  # type: ignore[call-arg]
        betas=["web-fetch-2025-09-10"],
        output_version=output_version,
    )

    if output_version == "v0":
        call_key = "server_tool_use"
        result_key = "web_fetch_tool_result"
    else:
        # v1
        call_key = "server_tool_call"
        result_key = "server_tool_result"

    tool = {
        "type": "web_fetch_20250910",
        "name": "web_fetch",
        "max_uses": 1,
        "citations": {"enabled": True},
    }
    llm_with_tools = llm.bind_tools([tool])

    input_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Fetch the content at https://docs.langchain.com and analyze",
            },
        ],
    }
    response = llm_with_tools.invoke([input_message])
    assert all(isinstance(block, dict) for block in response.content)
    block_types = {block["type"] for block in response.content}  # type: ignore[index]
    assert block_types == {"text", call_key, result_key}

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm_with_tools.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk

    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    block_types = {block["type"] for block in full.content}  # type: ignore[index]
    assert block_types == {"text", call_key, result_key}

    # Test we can pass back in
    next_message = {
        "role": "user",
        "content": "What does the site you just fetched say about models?",
    }
    _ = llm_with_tools.invoke(
        [input_message, full, next_message],
    )