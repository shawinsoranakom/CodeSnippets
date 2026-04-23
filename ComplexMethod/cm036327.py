async def test_engine_core_client_asyncio(
    monkeypatch: pytest.MonkeyPatch,
    subprocess_echo_patch,
):
    with monkeypatch.context() as m:
        # Monkey-patch core engine utility function to test.
        m.setattr(EngineCore, "echo", echo, raising=False)

        engine_args = EngineArgs(model=MODEL_NAME, enforce_eager=True)
        vllm_config = engine_args.create_engine_config(
            usage_context=UsageContext.UNKNOWN_CONTEXT
        )
        executor_class = Executor.get_class(vllm_config)

        with set_default_torch_num_threads(1):
            client = EngineCoreClient.make_client(
                multiprocess_mode=True,
                asyncio_mode=True,
                vllm_config=vllm_config,
                executor_class=executor_class,
                log_stats=True,
            )

        try:
            MAX_TOKENS = 20
            params = SamplingParams(max_tokens=MAX_TOKENS)
            """Normal Request Cycle."""

            requests = [make_request(params) for _ in range(10)]
            request_ids = [req.request_id for req in requests]

            # Add requests to the engine.
            for request in requests:
                await client.add_request_async(request)
                await asyncio.sleep(0.01)

            outputs: dict[str, list] = {req_id: [] for req_id in request_ids}
            await loop_until_done_async(client, outputs)

            for req_id in request_ids:
                assert len(outputs[req_id]) == MAX_TOKENS, (
                    f"{outputs[req_id]=}, {MAX_TOKENS=}"
                )
            """Abort Request Cycle."""

            # Add requests to the engine.
            for idx, request in enumerate(requests):
                await client.add_request_async(request)
                await asyncio.sleep(0.01)
                if idx % 2 == 0:
                    await client.abort_requests_async([request.request_id])

            outputs = {req_id: [] for req_id in request_ids}
            await loop_until_done_async(client, outputs)

            for idx, req_id in enumerate(request_ids):
                if idx % 2 == 0:
                    assert len(outputs[req_id]) < MAX_TOKENS, (
                        f"{len(outputs[req_id])=}, {MAX_TOKENS=}"
                    )
                else:
                    assert len(outputs[req_id]) == MAX_TOKENS, (
                        f"{len(outputs[req_id])=}, {MAX_TOKENS=}"
                    )
            """Utility method invocation"""

            core_client: AsyncMPClient = client

            result = await core_client.call_utility_async("echo", "testarg")
            assert result == "testarg"

            with pytest.raises(Exception) as e_info:
                await core_client.call_utility_async("echo", None, "help!")

            assert str(e_info.value) == "Call to echo method failed: help!"

            # Test that cancelling the utility call doesn't destabilize the
            # engine.
            util_task = asyncio.create_task(
                core_client.call_utility_async("echo", "testarg2", None, 0.5)
            )  # sleep for 0.5 sec
            await asyncio.sleep(0.05)
            cancelled = util_task.cancel()
            assert cancelled

            # Ensure client is still functional. The engine runs utility
            # methods in a single thread so this request won't be processed
            # until the cancelled sleeping one is complete.
            result = await asyncio.wait_for(
                core_client.call_utility_async("echo", "testarg3"), timeout=1.0
            )
            assert result == "testarg3"
        finally:
            client.shutdown()