def test_stream_reasoning_summary(
    output_version: Literal["v0", "responses/v1", "v1"],
) -> None:
    llm = ChatOpenAI(
        model="o4-mini",
        # Routes to Responses API if `reasoning` is set.
        reasoning={"effort": "medium", "summary": "auto"},
        output_version=output_version,
    )
    message_1 = {
        "role": "user",
        "content": "What was the third tallest buliding in the year 2000?",
    }
    response_1: BaseMessageChunk | None = None
    for chunk in llm.stream([message_1]):
        assert isinstance(chunk, AIMessageChunk)
        response_1 = chunk if response_1 is None else response_1 + chunk
    assert isinstance(response_1, AIMessageChunk)
    if output_version == "v0":
        reasoning = response_1.additional_kwargs["reasoning"]
        assert set(reasoning.keys()) == {"id", "type", "summary"}
        summary = reasoning["summary"]
        assert isinstance(summary, list)
        for block in summary:
            assert isinstance(block, dict)
            assert isinstance(block["type"], str)
            assert isinstance(block["text"], str)
            assert block["text"]
    elif output_version == "responses/v1":
        reasoning = next(
            block
            for block in response_1.content
            if block["type"] == "reasoning"  # type: ignore[index]
        )
        if isinstance(reasoning, str):
            reasoning = json.loads(reasoning)
        assert set(reasoning.keys()) == {"id", "type", "summary", "index"}
        summary = reasoning["summary"]
        assert isinstance(summary, list)
        for block in summary:
            assert isinstance(block, dict)
            assert isinstance(block["type"], str)
            assert isinstance(block["text"], str)
            assert block["text"]
    else:
        # v1
        total_reasoning_blocks = 0
        for block in response_1.content_blocks:
            if block["type"] == "reasoning":
                total_reasoning_blocks += 1
                assert isinstance(block.get("id"), str)
                assert block.get("id", "").startswith("rs_")
                assert isinstance(block.get("reasoning"), str)
                assert isinstance(block.get("index"), str)
        assert (
            total_reasoning_blocks > 1
        )  # This query typically generates multiple reasoning blocks

    # Check we can pass back summaries
    message_2 = {"role": "user", "content": "Thank you."}
    response_2 = llm.invoke([message_1, response_1, message_2])
    assert isinstance(response_2, AIMessage)