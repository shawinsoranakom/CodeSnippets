async def test_multi_abort(output_kind: RequestOutputKind):
    with ExitStack() as after:
        with set_default_torch_num_threads(1):
            engine = AsyncLLM.from_engine_args(TEXT_ENGINE_ARGS)
        after.callback(engine.shutdown)

        NUM_REQUESTS = 50
        NUM_EXPECTED_TOKENS = 100
        NUM_EXPECTED_TOKENS_LONG = 50000
        REQUEST_IDS_TO_ABORT = [5, 10, 15, 20, 25]
        PARALLEL_SAMPLE_REQ_IDS = [5, 15, 30, 35]

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
                    generate(
                        engine, request_id, TEXT_PROMPT, output_kind, max_tokens, n
                    )
                )
            )

        # Let requests start
        await asyncio.sleep(0.5)

        # Use multi-abort to abort multiple requests at once
        abort_request_ids = [request_ids[i] for i in REQUEST_IDS_TO_ABORT]
        await engine.abort(abort_request_ids, internal=False)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify results
        for idx, result in enumerate(results):
            if idx in REQUEST_IDS_TO_ABORT:
                # Aborted requests should return partial results
                assert isinstance(result, tuple), (
                    f"Request {idx} should have completed with partial results"
                )
                num_generated_tokens, request_id = result
                # Should have generated some tokens before abort
                assert num_generated_tokens > 0, (
                    f"Aborted request {request_id} should have generated some tokens"
                )
            else:
                # Non-aborted requests should complete normally
                assert isinstance(result, tuple), (
                    f"Request {idx} should have completed successfully"
                )
                num_generated_tokens, request_id = result
                n = 3 if idx in PARALLEL_SAMPLE_REQ_IDS else 1
                expected_tokens = NUM_EXPECTED_TOKENS * n
                assert num_generated_tokens == expected_tokens, (
                    f"{request_id} generated {num_generated_tokens} but "
                    f"expected {expected_tokens}"
                )

        # Make sure all aborted requests were cleaned up
        assert not engine.output_processor.has_unfinished_requests()