def test_engine_core_client(
    monkeypatch: pytest.MonkeyPatch,
    multiprocessing_mode: bool,
    subprocess_echo_patch,
):
    with monkeypatch.context() as m:
        # Monkey-patch core engine utility function to test.
        m.setattr(EngineCore, "echo", echo, raising=False)

        engine_args = EngineArgs(model=MODEL_NAME, enforce_eager=True)
        vllm_config = engine_args.create_engine_config(UsageContext.UNKNOWN_CONTEXT)
        executor_class = Executor.get_class(vllm_config)

        with set_default_torch_num_threads(1):
            client = EngineCoreClient.make_client(
                multiprocess_mode=multiprocessing_mode,
                asyncio_mode=False,
                vllm_config=vllm_config,
                executor_class=executor_class,
                log_stats=False,
            )

        MAX_TOKENS = 20
        params = SamplingParams(max_tokens=MAX_TOKENS)
        """Normal Request Cycle."""
        requests = [make_request(params) for _ in range(10)]
        request_ids = [req.request_id for req in requests]

        # Add requests to the engine.
        for request in requests:
            client.add_request(request)
            time.sleep(0.01)

        outputs: dict[str, list] = {req_id: [] for req_id in request_ids}
        loop_until_done(client, outputs)

        for req_id in request_ids:
            assert len(outputs[req_id]) == MAX_TOKENS, (
                f"{outputs[req_id]=}, {MAX_TOKENS=}"
            )
        """Abort Request Cycle."""

        # Note: this code pathway will only work for multiprocessing
        # since we have to call get_output() explicitly

        # Add requests to the engine.
        for idx, request in enumerate(requests):
            client.add_request(request)
            time.sleep(0.01)
            if idx % 2 == 0:
                client.abort_requests([request.request_id])

        outputs = {req_id: [] for req_id in request_ids}
        loop_until_done(client, outputs)

        for idx, req_id in enumerate(request_ids):
            if idx % 2 == 0:
                assert len(outputs[req_id]) < MAX_TOKENS, (
                    f"{len(outputs[req_id])=}, {MAX_TOKENS=}"
                )
            else:
                assert len(outputs[req_id]) == MAX_TOKENS, (
                    f"{len(outputs[req_id])=}, {MAX_TOKENS=}"
                )
        """Abort after request is finished."""

        # Note: this code pathway will only work for multiprocessing
        # since we have to call get_output() explicitly

        request = requests[0]
        client.add_request(request)
        time.sleep(10.0)

        client.abort_requests([request.request_id])

        if multiprocessing_mode:
            """Utility method invocation"""

            core_client: SyncMPClient = client

            result = core_client.call_utility("echo", "testarg")
            assert result == "testarg"

            with pytest.raises(Exception) as e_info:
                core_client.call_utility("echo", None, "help!")

            assert str(e_info.value) == "Call to echo method failed: help!"