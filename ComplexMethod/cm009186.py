def test__construct_lc_result_from_responses_api_basic_text_response() -> None:
    """Test a basic text response with no tools or special features."""
    response = Response(
        id="resp_123",
        created_at=1234567890,
        model="gpt-4o",
        object="response",
        parallel_tool_calls=True,
        tools=[],
        tool_choice="auto",
        output=[
            ResponseOutputMessage(
                type="message",
                id="msg_123",
                content=[
                    ResponseOutputText(
                        type="output_text", text="Hello, world!", annotations=[]
                    )
                ],
                role="assistant",
                status="completed",
            )
        ],
        usage=ResponseUsage(
            input_tokens=10,
            output_tokens=3,
            total_tokens=13,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
        ),
    )

    # v0
    result = _construct_lc_result_from_responses_api(response, output_version="v0")

    assert isinstance(result, ChatResult)
    assert len(result.generations) == 1
    assert isinstance(result.generations[0], ChatGeneration)
    assert isinstance(result.generations[0].message, AIMessage)
    assert result.generations[0].message.content == [
        {"type": "text", "text": "Hello, world!", "annotations": []}
    ]
    assert result.generations[0].message.id == "msg_123"
    assert result.generations[0].message.usage_metadata
    assert result.generations[0].message.usage_metadata["input_tokens"] == 10
    assert result.generations[0].message.usage_metadata["output_tokens"] == 3
    assert result.generations[0].message.usage_metadata["total_tokens"] == 13
    assert result.generations[0].message.response_metadata["id"] == "resp_123"
    assert result.generations[0].message.response_metadata["model_name"] == "gpt-4o"

    # responses/v1
    result = _construct_lc_result_from_responses_api(response)
    assert result.generations[0].message.content == [
        {"type": "text", "text": "Hello, world!", "annotations": [], "id": "msg_123"}
    ]
    assert result.generations[0].message.id == "resp_123"
    assert result.generations[0].message.response_metadata["id"] == "resp_123"