def test_reasoning_v1() -> None:
    model = ChatMistralAI(model="magistral-medium-latest", output_version="v1")  # type: ignore[call-arg]
    input_message = {
        "role": "user",
        "content": "Hello, my name is Bob.",
    }
    full: AIMessageChunk | None = None
    chunks = []
    for chunk in model.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
        chunks.append(chunk)
    assert isinstance(full, AIMessageChunk)
    reasoning_blocks = 0
    for block in full.content:
        if isinstance(block, dict) and block.get("type") == "reasoning":
            reasoning_blocks += 1
            assert isinstance(block.get("reasoning"), str)
    assert reasoning_blocks > 0

    next_message = {"role": "user", "content": "What is my name?"}
    _ = model.invoke([input_message, full, next_message])