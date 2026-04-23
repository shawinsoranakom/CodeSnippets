def test_engine_core_concurrent_batches():
    """
    Test that the engine can handle multiple concurrent batches.
    """

    def make_request_with_max_tokens(req_id: str, max_tokens: int) -> EngineCoreRequest:
        request = make_request()
        request.request_id = req_id
        request.sampling_params.max_tokens = max_tokens
        return request

    class DummyExecutor(UniProcExecutor):
        def initialize_from_config(self, kv_cache_configs: list[KVCacheConfig]) -> None:
            super().initialize_from_config(kv_cache_configs)

            # Create a thread pool with a single worker
            self.thread_pool = ThreadPoolExecutor(max_workers=1)

        def execute_model(
            self,
            scheduler_output,
            non_block=False,
        ) -> Future[ModelRunnerOutput | None]:
            """Make execute_model non-blocking."""

            # DummyExecutor used only for testing async case.
            assert non_block

            def _execute():
                output = self.collective_rpc("execute_model", args=(scheduler_output,))
                # Make a copy because output[0] may be reused
                # by the next batch.
                return copy.deepcopy(output[0])

            # Use the thread pool instead of creating a new thread
            return self.thread_pool.submit(_execute)

        def sample_tokens(
            self, grammar_output, non_block=False
        ) -> Future[ModelRunnerOutput]:
            """Make sample_tokens non-blocking."""

            # DummyExecutor used only for testing async case.
            assert non_block

            def _execute():
                output = self.collective_rpc("sample_tokens", args=(grammar_output,))
                # Make a copy because output[0] may be reused
                # by the next batch.
                return copy.deepcopy(output[0])

            # Use the thread pool instead of creating a new thread
            return self.thread_pool.submit(_execute)

        @property
        def max_concurrent_batches(self) -> int:
            return 2

        def shutdown(self):
            if hasattr(self, "thread_pool"):
                self.thread_pool.shutdown(wait=False)

    engine_args = EngineArgs(
        model=MODEL_NAME,
        # To test concurrent batches.
        max_num_seqs=2,
        # Avoid all requests being scheduled once.
        enable_prefix_caching=False,
        max_num_batched_tokens=10,
        # Reduce startup time.
        enforce_eager=True,
        # Test concurrent batch behaviour independently of async scheduling.
        async_scheduling=False,
    )
    vllm_config = engine_args.create_engine_config()
    with set_default_torch_num_threads(1):
        engine_core = EngineCore(
            vllm_config=vllm_config, log_stats=False, executor_class=DummyExecutor
        )
    assert engine_core.batch_queue is not None

    # Add two requests in a row. Each request have 12 prompt tokens.
    req0 = make_request_with_max_tokens("0", 5)
    engine_core.add_request(*engine_core.preprocess_add_request(req0))
    req1 = make_request_with_max_tokens("1", 5)
    engine_core.add_request(*engine_core.preprocess_add_request(req1))

    # Schedule Batch 1: (10, req0)
    assert engine_core.step_with_batch_queue()[0] is None
    assert len(engine_core.batch_queue) == 1
    scheduler_output = engine_core.batch_queue[-1][1]
    assert scheduler_output.num_scheduled_tokens["0"] == 10
    # num_computed_tokens should have been updated immediately.
    assert engine_core.scheduler.requests[req0.request_id].num_computed_tokens == 10

    # Schedule Batch 2: (2, req0), (8, req1)
    assert engine_core.step_with_batch_queue()[0] == {}
    assert len(engine_core.batch_queue) == 1
    scheduler_output = engine_core.batch_queue[-1][1]
    assert scheduler_output.num_scheduled_tokens["0"] == 2
    assert scheduler_output.num_scheduled_tokens["1"] == 8
    # num_computed_tokens should have been updated immediately.
    assert engine_core.scheduler.requests["0"].num_computed_tokens == 12
    assert engine_core.scheduler.requests["1"].num_computed_tokens == 8

    assert engine_core.scheduler.get_num_unfinished_requests() == 2

    # Finish Batch 1 and schedule Batch 3: (4, req1).
    # Note that req0 cannot be scheduled
    # because it is in the decoding stage now.
    engine_core.step_with_batch_queue()
    assert len(engine_core.batch_queue) == 1
    scheduler_output = engine_core.batch_queue[-1][1]
    assert scheduler_output.num_scheduled_tokens["1"] == 4

    # Finish Batch 2. Get first token of req0.
    # Schedule Batch 4: (1, req0).
    output = engine_core.step_with_batch_queue()[0].get(0)
    assert output is not None
    assert len(output.outputs) == 1
    assert engine_core.scheduler.requests[req0.request_id].num_tokens == 13
    scheduler_output = engine_core.batch_queue[-1][1]
    assert scheduler_output.num_scheduled_tokens["0"] == 1

    # Finish Batch 3. Get first token of req1. Schedule Batch 5: (1, req1).
    output = engine_core.step_with_batch_queue()[0].get(0)
    assert output is not None
    assert len(output.outputs) == 1
    assert engine_core.scheduler.requests[req1.request_id].num_tokens == 13
    scheduler_output = engine_core.batch_queue[-1][1]
    assert scheduler_output.num_scheduled_tokens["1"] == 1

    # Loop until req0 is finished.
    req_id = 0
    expected_num_tokens = [
        engine_core.scheduler.requests["0"].num_tokens + 1,
        engine_core.scheduler.requests["1"].num_tokens + 1,
    ]
    while engine_core.scheduler.get_num_unfinished_requests() == 2:
        output = engine_core.step_with_batch_queue()[0]
        # Every step consumes an output.
        assert output is not None
        assert len(output[0].outputs) == 1
        if req_id in engine_core.scheduler.requests:
            assert (
                engine_core.scheduler.requests[req_id].num_tokens
                == expected_num_tokens[req_id]
            )
        expected_num_tokens[req_id] += 1
        req_id = (req_id + 1) % 2