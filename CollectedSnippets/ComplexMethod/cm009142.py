def test_image_generation_streaming(
    output_version: Literal["v0", "responses/v1"],
) -> None:
    """Test image generation streaming."""
    llm = ChatOpenAI(
        model="gpt-4.1", use_responses_api=True, output_version=output_version
    )
    tool = {
        "type": "image_generation",
        # For testing purposes let's keep the quality low, so the test runs faster.
        "quality": "low",
        "output_format": "jpeg",
        "output_compression": 100,
        "size": "1024x1024",
    }

    # Example tool output for an image
    # {
    #     "background": "opaque",
    #     "id": "ig_683716a8ddf0819888572b20621c7ae4029ec8c11f8dacf8",
    #     "output_format": "png",
    #     "quality": "high",
    #     "revised_prompt": "A fluffy, fuzzy cat sitting calmly, with soft fur, bright "
    #     "eyes, and a cute, friendly expression. The background is "
    #     "simple and light to emphasize the cat's texture and "
    #     "fluffiness.",
    #     "size": "1024x1024",
    #     "status": "completed",
    #     "type": "image_generation_call",
    #     "result": # base64 encode image data
    # }

    expected_keys = {
        "id",
        "index",
        "background",
        "output_format",
        "quality",
        "result",
        "revised_prompt",
        "size",
        "status",
        "type",
    }

    full: BaseMessageChunk | None = None
    for chunk in llm.stream("Draw a random short word in green font.", tools=[tool]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    complete_ai_message = cast(AIMessageChunk, full)
    # At the moment, the streaming API does not pick up annotations fully.
    # So the following check is commented out.
    # _check_response(complete_ai_message)
    if output_version == "v0":
        assert complete_ai_message.additional_kwargs["tool_outputs"]
        tool_output = complete_ai_message.additional_kwargs["tool_outputs"][0]
        assert set(tool_output.keys()).issubset(expected_keys)
    else:
        # "responses/v1"
        tool_output = next(
            block
            for block in complete_ai_message.content
            if isinstance(block, dict) and block["type"] == "image_generation_call"
        )
        assert set(tool_output.keys()).issubset(expected_keys)