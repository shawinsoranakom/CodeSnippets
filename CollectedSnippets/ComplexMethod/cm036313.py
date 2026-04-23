async def test_abort(
    output_kind: RequestOutputKind,
    engine_args: AsyncEngineArgs,
    prompt: PromptType,
):
    with ExitStack() as after:
        with set_default_torch_num_threads(1):
            engine = AsyncLLM.from_engine_args(engine_args)
        after.callback(engine.shutdown)

        NUM_REQUESTS = 100
        NUM_EXPECTED_TOKENS = 100
        NUM_EXPECTED_TOKENS_LONG = 50000
        REQUEST_IDS_TO_ABORT = range(1, 100, 10)
        PARALLEL_SAMPLE_REQ_IDS = range(1, 100, 15)

        request_ids = [f"request-{i}" for i in range(NUM_REQUESTS)]

        # Create concurrent requests.
        tasks: list[asyncio.Task] = []
        for idx, request_id in enumerate(request_ids):
            max_tokens = (
                NUM_EXPECTED_TOKENS_LONG
                if (idx in REQUEST_IDS_TO_ABORT)
                else NUM_EXPECTED_TOKENS
            )
            n = 3 if idx in PARALLEL_SAMPLE_REQ_IDS else 1
            tasks.append(
                asyncio.create_task(
                    generate(engine, request_id, prompt, output_kind, max_tokens, n)
                )
            )

        # API server cancels requests when they disconnect.
        for idx in REQUEST_IDS_TO_ABORT:
            tasks[idx].cancel()
            await asyncio.sleep(0.1)

        # Confirm the other requests are okay.
        for idx, task in enumerate(tasks):
            # Confirm that it was actually canceled.
            if idx in REQUEST_IDS_TO_ABORT:
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                # Otherwise, make sure the request was not impacted.
                num_generated_tokens, request_id = await task
                n = 3 if idx in PARALLEL_SAMPLE_REQ_IDS else 1
                expected_tokens = NUM_EXPECTED_TOKENS * n
                assert num_generated_tokens == expected_tokens, (
                    f"{request_id} generated {num_generated_tokens} but "
                    f"expected {expected_tokens}"
                )

        # Make sure all aborted requests were really aborted.
        assert not engine.output_processor.has_unfinished_requests()

        # Confirm we can do another generation.
        request_id = f"request-{REQUEST_IDS_TO_ABORT[0]}"
        task = asyncio.create_task(
            generate(engine, request_id, prompt, output_kind, NUM_EXPECTED_TOKENS)
        )
        num_generated_tokens, request_id = await task
        assert num_generated_tokens == NUM_EXPECTED_TOKENS
        assert not engine.output_processor.has_unfinished_requests()