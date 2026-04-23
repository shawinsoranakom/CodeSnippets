async def test_streaming_output_consistency(client: OpenAI, model_name: str):
    """Test that streaming delta text matches the final response output_text.

    This test verifies that when using streaming mode:
    1. The concatenated text from all 'response.output_text.delta' events
    2. Matches the 'output_text' in the final 'response.completed' event
    """
    response = await client.responses.create(
        model=model_name,
        input="Say hello in one sentence.",
        stream=True,
    )

    events = []
    async for event in response:
        events.append(event)

    assert len(events) > 0

    # Concatenate all delta text from streaming events
    streaming_text = "".join(
        event.delta for event in events if event.type == "response.output_text.delta"
    )

    # Get the final response from the last event
    response_completed_event = events[-1]
    assert response_completed_event.type == "response.completed"
    assert response_completed_event.response.status == "completed"

    # Get output_text from the final response
    final_output_text = response_completed_event.response.output_text

    # Verify final response has output
    assert len(response_completed_event.response.output) > 0

    # Verify streaming text matches final output_text
    assert streaming_text == final_output_text, (
        f"Streaming text does not match final output_text.\n"
        f"Streaming: {streaming_text!r}\n"
        f"Final: {final_output_text!r}"
    )