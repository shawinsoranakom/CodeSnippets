def test_image_generation_streaming_v1() -> None:
    """Test image generation streaming."""
    llm = ChatOpenAI(model="gpt-4.1", use_responses_api=True, output_version="v1")
    tool = {
        "type": "image_generation",
        "quality": "low",
        "output_format": "jpeg",
        "output_compression": 100,
        "size": "1024x1024",
    }

    standard_keys = {"type", "base64", "mime_type", "id", "index"}
    extra_keys = {
        "background",
        "output_format",
        "quality",
        "revised_prompt",
        "size",
        "status",
    }

    full: BaseMessageChunk | None = None
    for chunk in llm.stream("Draw a random short word in green font.", tools=[tool]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    complete_ai_message = cast(AIMessageChunk, full)

    tool_output = next(
        block
        for block in complete_ai_message.content
        if isinstance(block, dict) and block["type"] == "image"
    )
    assert set(standard_keys).issubset(tool_output.keys())
    assert set(extra_keys).issubset(tool_output["extras"].keys())