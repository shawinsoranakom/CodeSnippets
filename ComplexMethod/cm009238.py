def test_citations(output_version: Literal["v0", "v1"]) -> None:
    llm = ChatAnthropic(model=MODEL_NAME, output_version=output_version)  # type: ignore[call-arg]
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "content",
                        "content": [
                            {"type": "text", "text": "The grass is green"},
                            {"type": "text", "text": "The sky is blue"},
                        ],
                    },
                    "citations": {"enabled": True},
                },
                {"type": "text", "text": "What color is the grass and sky?"},
            ],
        },
    ]
    response = llm.invoke(messages)
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, list)
    if output_version == "v1":
        assert any("annotations" in block for block in response.content)
    else:
        assert any("citations" in block for block in response.content)

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream(messages):
        full = cast("BaseMessageChunk", chunk) if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    assert not any("citation" in block for block in full.content)
    if output_version == "v1":
        assert any("annotations" in block for block in full.content)
    else:
        assert any("citations" in block for block in full.content)

    # Test pass back in
    next_message = {
        "role": "user",
        "content": "Can you comment on the citations you just made?",
    }
    _ = llm.invoke([*messages, full, next_message])