async def test_streaming_reasoning_tokens_e2e(client: OpenAI, model_name: str):
    """Verify final usage includes reasoning_tokens in streaming mode."""
    response = await client.responses.create(
        model=model_name,
        input="Compute 17 * 19 and explain briefly.",
        reasoning={"effort": "low"},
        temperature=0.0,
        stream=True,
    )

    completed_event = None
    async for event in response:
        if event.type == "response.completed":
            completed_event = event

    assert completed_event is not None
    assert completed_event.response.status == "completed"
    assert completed_event.response.usage is not None
    assert completed_event.response.usage.output_tokens_details is not None
    assert completed_event.response.usage.output_tokens_details.reasoning_tokens > 0, (
        "Expected reasoning_tokens > 0 for streamed Qwen3 response."
    )