def test_image_generation_multi_turn(
    output_version: Literal["v0", "responses/v1"],
) -> None:
    """Test multi-turn editing of image generation by passing in history."""
    # Test multi-turn
    llm = ChatOpenAI(
        model="gpt-4.1", use_responses_api=True, output_version=output_version
    )
    # Test invocation
    tool = {
        "type": "image_generation",
        # For testing purposes let's keep the quality low, so the test runs faster.
        "quality": "low",
        "output_format": "jpeg",
        "output_compression": 100,
        "size": "1024x1024",
    }
    llm_with_tools = llm.bind_tools([tool])

    chat_history: list[MessageLikeRepresentation] = [
        {"role": "user", "content": "Draw a random short word in green font."}
    ]
    ai_message = llm_with_tools.invoke(chat_history)
    assert isinstance(ai_message, AIMessage)
    _check_response(ai_message)

    expected_keys = {
        "id",
        "background",
        "output_format",
        "quality",
        "result",
        "revised_prompt",
        "size",
        "status",
        "type",
    }

    if output_version == "v0":
        tool_output = ai_message.additional_kwargs["tool_outputs"][0]
        assert set(tool_output.keys()).issubset(expected_keys)
    elif output_version == "responses/v1":
        tool_output = next(
            block
            for block in ai_message.content
            if isinstance(block, dict) and block["type"] == "image_generation_call"
        )
        assert set(tool_output.keys()).issubset(expected_keys)
    else:
        standard_keys = {"type", "base64", "id", "status"}
        tool_output = next(
            block
            for block in ai_message.content
            if isinstance(block, dict) and block["type"] == "image"
        )
        assert set(standard_keys).issubset(tool_output.keys())

    # Example tool output for an image (v0)
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

    chat_history.extend(
        [
            # AI message with tool output
            ai_message,
            # New request
            {
                "role": "user",
                "content": (
                    "Now, change the font to blue. Keep the word and everything else "
                    "the same."
                ),
            },
        ]
    )

    ai_message2 = llm_with_tools.invoke(chat_history)
    assert isinstance(ai_message2, AIMessage)
    _check_response(ai_message2)

    if output_version == "v0":
        tool_output = ai_message2.additional_kwargs["tool_outputs"][0]
        assert set(tool_output.keys()).issubset(expected_keys)
    else:
        # "responses/v1"
        tool_output = next(
            block
            for block in ai_message2.content
            if isinstance(block, dict) and block["type"] == "image_generation_call"
        )
        assert set(tool_output.keys()).issubset(expected_keys)