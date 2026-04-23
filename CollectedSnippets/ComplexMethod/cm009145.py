def test_image_generation_multi_turn_v1() -> None:
    """Test multi-turn editing of image generation by passing in history."""
    # Test multi-turn
    llm = ChatOpenAI(model="gpt-4.1", use_responses_api=True, output_version="v1")
    # Test invocation
    tool = {
        "type": "image_generation",
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

    standard_keys = {"type", "base64", "mime_type", "id"}
    extra_keys = {
        "background",
        "output_format",
        "quality",
        "revised_prompt",
        "size",
        "status",
    }

    tool_output = next(
        block
        for block in ai_message.content
        if isinstance(block, dict) and block["type"] == "image"
    )
    assert set(standard_keys).issubset(tool_output.keys())
    assert set(extra_keys).issubset(tool_output["extras"].keys())

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

    tool_output = next(
        block
        for block in ai_message2.content
        if isinstance(block, dict) and block["type"] == "image"
    )
    assert set(standard_keys).issubset(tool_output.keys())
    assert set(extra_keys).issubset(tool_output["extras"].keys())