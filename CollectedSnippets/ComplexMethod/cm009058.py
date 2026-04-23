def test_reasoning() -> None:
    model = ChatMistralAI(model="magistral-medium-latest")  # type: ignore[call-arg]
    input_message = {
        "role": "user",
        "content": "Hello, my name is Bob.",
    }
    full: AIMessageChunk | None = None
    for chunk in model.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    thinking_blocks = 0
    for i, block in enumerate(full.content):
        if isinstance(block, dict) and block.get("type") == "thinking":
            thinking_blocks += 1
            reasoning_block = full.content_blocks[i]
            assert reasoning_block["type"] == "reasoning"
            assert isinstance(reasoning_block.get("reasoning"), str)
    assert thinking_blocks > 0

    next_message = {"role": "user", "content": "What is my name?"}
    _ = model.invoke([input_message, full, next_message])