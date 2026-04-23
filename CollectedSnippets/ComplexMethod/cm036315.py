async def test_mid_stream_cancellation(
    engine_args: AsyncEngineArgs, prompt: PromptType
):
    """Test that requests can be cancelled mid-stream."""
    with ExitStack() as after:
        with set_default_torch_num_threads(1):
            engine = AsyncLLM.from_engine_args(engine_args)
        after.callback(engine.shutdown)

        NUM_REQUESTS = 100
        NUM_TOKENS = 1000
        NUM_EXPECTED_TOKENS = 20

        request_ids = [f"request-{i}" for i in range(NUM_REQUESTS)]

        # Create concurrent requests that will be cancelled mid-stream
        tasks = []
        for request_id in request_ids:
            tasks.append(
                asyncio.create_task(
                    generate(
                        engine,
                        request_id,
                        prompt,
                        RequestOutputKind.DELTA,
                        NUM_TOKENS,
                        cancel_after=NUM_EXPECTED_TOKENS,
                    )
                )
            )

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        # Verify all tasks were cancelled at the expected point
        for num_generated_tokens, request_id in results:
            assert num_generated_tokens == NUM_EXPECTED_TOKENS, (
                f"{request_id} generated {num_generated_tokens} tokens but "
                f"expected to cancel after {NUM_EXPECTED_TOKENS}"
            )

        # Make sure no requests are left hanging
        assert not engine.output_processor.has_unfinished_requests()

        # Confirm we can reuse the request id after the cancellations.
        request_id = request_ids[0]
        task = asyncio.create_task(
            generate(
                engine, request_id, prompt, RequestOutputKind.DELTA, NUM_EXPECTED_TOKENS
            )
        )
        num_generated_tokens, request_id = await task
        assert num_generated_tokens == NUM_EXPECTED_TOKENS
        assert not engine.output_processor.has_unfinished_requests()