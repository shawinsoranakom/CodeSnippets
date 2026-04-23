async def test_streaming_input_delayed_generator_exit(engine: AsyncLLM):
    """Test that output generator exits when input generator closes after outputs.

    This tests the case where:
    1. Multiple inputs are sent and fully processed
    2. The engine has finished
    3. The input generator doesn't exit until after the engine finishes
    4. The output generator should exit properly once the input generator exits
    """
    request_id = "test_delayed_exit"
    sampling_params = get_sampling_params(max_tokens=10)

    engine_finished_event = asyncio.Event()
    input_generator_exited = False
    finish_count = 0

    async def delayed_exit_input_generator() -> AsyncGenerator[StreamingInput, None]:
        nonlocal input_generator_exited
        # Send all inputs immediately
        yield StreamingInput(prompt="Hello, my name is")
        yield StreamingInput(prompt=" Alice")

        # Wait until the engine has finished generating before exiting
        await engine_finished_event.wait()

        # Add a small delay to ensure we're testing the "delayed exit" case
        await asyncio.sleep(0.1)
        input_generator_exited = True

    outputs: list[RequestOutput] = []
    full_text = ""

    async for output in engine.generate(
        delayed_exit_input_generator(), sampling_params, request_id
    ):
        outputs.append(output)
        if output.outputs and output.outputs[0].text:
            full_text += output.outputs[0].text

        # Signal when the engine finishes both input chunks (each gets a finish_reason)
        # Note: output.finished will be False while input stream is open
        if output.outputs and output.outputs[0].finish_reason is not None:
            finish_count += 1
            if finish_count == 2:
                engine_finished_event.set()

    # Verify the input generator exited properly
    assert input_generator_exited, (
        "Input generator should have exited after engine finished"
    )

    # Verify we got outputs
    assert len(outputs) > 0, "Should have received outputs"

    # Verify we generated some text
    assert len(full_text) > 0, "Should have generated text"

    # Verify the session is cleaned up
    assert not engine.output_processor.has_unfinished_requests(), (
        "Should have no unfinished requests"
    )

    print(f"Delayed exit test passed. Generated: {full_text}")