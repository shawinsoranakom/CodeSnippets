def test_thinking_v1() -> None:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",  # type: ignore[call-arg]
        max_tokens=5_000,  # type: ignore[call-arg]
        thinking={"type": "enabled", "budget_tokens": 2_000},
        output_version="v1",
    )

    input_message = {"role": "user", "content": "Hello"}
    response = llm.invoke([input_message])
    assert any("reasoning" in block for block in response.content)
    for block in response.content:
        assert isinstance(block, dict)
        if block["type"] == "reasoning":
            assert set(block.keys()) == {"type", "reasoning", "extras"}
            assert block["reasoning"]
            assert isinstance(block["reasoning"], str)
            signature = block["extras"]["signature"]
            assert signature
            assert isinstance(signature, str)

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream([input_message]):
        full = cast(BaseMessageChunk, chunk) if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    assert any("reasoning" in block for block in full.content)
    for block in full.content:
        assert isinstance(block, dict)
        if block["type"] == "reasoning":
            assert set(block.keys()) == {"type", "reasoning", "extras", "index"}
            assert block["reasoning"]
            assert isinstance(block["reasoning"], str)
            signature = block["extras"]["signature"]
            assert signature
            assert isinstance(signature, str)

    # Test pass back in
    next_message = {"role": "user", "content": "How are you?"}
    _ = llm.invoke([input_message, full, next_message])