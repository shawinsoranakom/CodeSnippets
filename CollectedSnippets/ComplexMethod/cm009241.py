def test_redacted_thinking(output_version: Literal["v0", "v1"]) -> None:
    llm = ChatAnthropic(
        # It appears that Sonnet 4.5 either: isn't returning redacted thinking blocks,
        # or the magic string is broken? Retry later once 3-7 finally removed
        model="claude-3-7-sonnet-latest",  # type: ignore[call-arg]
        max_tokens=5_000,  # type: ignore[call-arg]
        thinking={"type": "enabled", "budget_tokens": 2_000},
        output_version=output_version,
    )
    query = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"  # noqa: E501
    input_message = {"role": "user", "content": query}

    response = llm.invoke([input_message])
    value = None
    for block in response.content:
        assert isinstance(block, dict)
        if block["type"] == "redacted_thinking":
            value = block
        elif (
            block["type"] == "non_standard"
            and block["value"]["type"] == "redacted_thinking"
        ):
            value = block["value"]
        else:
            pass
        if value:
            assert set(value.keys()) == {"type", "data"}
            assert value["data"]
            assert isinstance(value["data"], str)
    assert value is not None

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream([input_message]):
        full = cast("BaseMessageChunk", chunk) if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    value = None
    for block in full.content:
        assert isinstance(block, dict)
        if block["type"] == "redacted_thinking":
            value = block
            assert set(value.keys()) == {"type", "data", "index"}
            assert "index" in block
        elif (
            block["type"] == "non_standard"
            and block["value"]["type"] == "redacted_thinking"
        ):
            value = block["value"]
            assert isinstance(value, dict)
            assert set(value.keys()) == {"type", "data"}
            assert "index" in block
        else:
            pass
        if value:
            assert value["data"]
            assert isinstance(value["data"], str)
    assert value is not None

    # Test pass back in
    next_message = {"role": "user", "content": "What?"}
    _ = llm.invoke([input_message, full, next_message])