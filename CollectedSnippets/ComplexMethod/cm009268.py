def test_reasoning(output_version: Literal["", "v1"]) -> None:
    """Test reasoning features.

    !!! note

        `grok-4` does not return `reasoning_content`, but may optionally return
        encrypted reasoning content if `use_encrypted_content` is set to `True`.
    """
    # Test reasoning effort
    if output_version:
        chat_model = ChatXAI(
            model="grok-3-mini",
            reasoning_effort="low",
            temperature=0,
            output_version=output_version,
        )
    else:
        chat_model = ChatXAI(
            model="grok-3-mini",
            reasoning_effort="low",
            temperature=0,
        )
    input_message = "What is 3^3?"
    response = chat_model.invoke(input_message)
    assert response.content
    assert response.additional_kwargs["reasoning_content"]

    ## Check output tokens
    usage_metadata = response.usage_metadata
    assert usage_metadata
    reasoning_tokens = usage_metadata.get("output_token_details", {}).get("reasoning")
    total_tokens = usage_metadata.get("output_tokens")
    assert total_tokens
    assert reasoning_tokens
    assert total_tokens > reasoning_tokens

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in chat_model.stream(input_message):
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.additional_kwargs["reasoning_content"]

    ## Check output tokens
    usage_metadata = full.usage_metadata
    assert usage_metadata
    reasoning_tokens = usage_metadata.get("output_token_details", {}).get("reasoning")
    total_tokens = usage_metadata.get("output_tokens")
    assert total_tokens
    assert reasoning_tokens
    assert total_tokens > reasoning_tokens

    # Check that we can access reasoning content blocks
    assert response.content_blocks
    reasoning_content = (
        block for block in response.content_blocks if block["type"] == "reasoning"
    )
    assert len(list(reasoning_content)) >= 1

    # Test that passing message with reasoning back in works
    follow_up_message = "Based on your reasoning, what is 4^4?"
    followup = chat_model.invoke([input_message, response, follow_up_message])
    assert followup.content
    assert followup.additional_kwargs["reasoning_content"]
    followup_reasoning = (
        block for block in followup.content_blocks if block["type"] == "reasoning"
    )
    assert len(list(followup_reasoning)) >= 1

    # Test passing in a ReasoningContentBlock
    response_metadata = {"model_provider": "xai"}
    if output_version:
        response_metadata["output_version"] = output_version
    msg_w_reasoning = AIMessage(
        content_blocks=response.content_blocks,
        response_metadata=response_metadata,
    )
    followup_2 = chat_model.invoke(
        [msg_w_reasoning, "Based on your reasoning, what is 5^5?"]
    )
    assert followup_2.content
    assert followup_2.additional_kwargs["reasoning_content"]