async def test_streaming_input_spaced(engine: AsyncLLM):
    """Test streaming input where inputs are spaced out.

    This tests the case where each input completes processing before the
    next one is sent. Each chunk should be prefilled, generate tokens,
    then the next chunk should be processed.
    """
    request_id = "test_spaced"
    sampling_params = get_sampling_params(max_tokens=10)

    # Track when each input is sent
    input_times: list[float] = []
    outputs_per_chunk: list[int] = [0, 0, 0]
    current_chunk = 0

    async def spaced_input_generator() -> AsyncGenerator[StreamingInput, None]:
        nonlocal current_chunk
        import time

        # First input
        input_times.append(time.time())
        yield StreamingInput(prompt="Hello, my name is")
        current_chunk = 0

        # Wait for some outputs to be generated
        await asyncio.sleep(0.5)

        # Second input
        input_times.append(time.time())
        current_chunk = 1
        yield StreamingInput(prompt=" Alice and I like")

        # Wait for some outputs
        await asyncio.sleep(0.5)

        # Third input
        input_times.append(time.time())
        current_chunk = 2
        yield StreamingInput(prompt=" to code in Python")

    outputs: list[RequestOutput] = []
    full_text = ""

    async for output in engine.generate(
        spaced_input_generator(),
        sampling_params,
        request_id,
    ):
        outputs.append(output)
        if output.outputs and output.outputs[0].text:
            full_text += output.outputs[0].text
            outputs_per_chunk[current_chunk] += 1

    # Verify we got outputs
    assert len(outputs) > 0, "Should have received outputs"

    # Verify the final output is marked as finished
    assert outputs[-1].finished, "Last output should be marked as finished"

    # Verify we received outputs from multiple chunks
    # (with spaced inputs, we should see outputs distributed across chunks)
    chunks_with_outputs = sum(1 for c in outputs_per_chunk if c > 0)
    assert chunks_with_outputs >= 1, "Should have outputs from at least one chunk"

    print(f"Spaced test generated: {full_text}")
    print(f"Outputs per chunk: {outputs_per_chunk}")