async def test_load(
    model: str,
    output_kind: RequestOutputKind,
    data_parallel_backend: str,
    async_scheduling: bool,
):
    if async_scheduling and data_parallel_backend == "ray":
        # TODO(NickLucche) Re-enable when async scheduling is supported
        pytest.skip("Async scheduling is not supported with ray")
    elif data_parallel_backend == "ray" and current_platform.is_rocm():
        pytest.skip(
            "Ray as the distributed executor backend is not supported with ROCm."
        )
    stats_loggers = {}

    @dataclass
    class SimpleStatsLogger(StatLoggerBase):
        init_count: int = 0
        finished_req_count: int = 0

        def __init__(self, vllm_config: VllmConfig, engine_index: int = 0):
            stats_loggers[engine_index] = self

        def record(
            self,
            scheduler_stats: SchedulerStats | None,
            iteration_stats: IterationStats | None,
            mm_cache_stats: MultiModalCacheStats | None = None,
            engine_idx: int = 0,
        ):
            if iteration_stats:
                self.finished_req_count += len(iteration_stats.finished_requests)

        def log_engine_initialized(self):
            self.init_count += 1

    with ExitStack() as after:
        prompt = "This is a test of data parallel"

        engine_args = AsyncEngineArgs(
            model=model,
            enforce_eager=True,
            tensor_parallel_size=int(os.getenv("TP_SIZE", 1)),
            data_parallel_size=DP_SIZE,
            data_parallel_backend=data_parallel_backend,
            async_scheduling=async_scheduling,
        )
        engine = AsyncLLM.from_engine_args(
            engine_args, stat_loggers=[SimpleStatsLogger]
        )
        after.callback(engine.shutdown)

        NUM_REQUESTS = 100
        NUM_EXPECTED_TOKENS = 10

        request_ids = [f"request-{i}" for i in range(NUM_REQUESTS)]

        # Create concurrent requests.
        tasks = []
        for request_id in request_ids:
            tasks.append(
                asyncio.create_task(
                    generate(
                        engine, request_id, prompt, output_kind, NUM_EXPECTED_TOKENS
                    )
                )
            )
            # Short sleep to ensure that requests are distributed.
            await asyncio.sleep(0.01)
        # Confirm that we got all the EXPECTED tokens from the requests.
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for task in pending:
            task.cancel()
        for task in done:
            num_generated_tokens, request_id = await task
            assert num_generated_tokens == NUM_EXPECTED_TOKENS, (
                f"{request_id} generated {num_generated_tokens} but "
                f"expected {NUM_EXPECTED_TOKENS}"
            )

        assert not engine.output_processor.has_unfinished_requests()

        # testing internals here which may break
        core_client: DPAsyncMPClient = engine.engine_core
        # the engines only synchronize stopping every N steps so
        # allow a small amount of time here.
        for _ in range(10):
            if not core_client.engines_running:
                break
            await asyncio.sleep(0.5)

        assert not core_client.engines_running
        assert not core_client.reqs_in_flight

        # Check that requests were distributed between the engines
        print(f"Stats loggers after test: {stats_loggers}")
        assert len(stats_loggers) == DP_SIZE
        assert stats_loggers[0].init_count == 1

        for sl in stats_loggers.values():
            slogger: SimpleStatsLogger = sl

            assert slogger.finished_req_count > NUM_REQUESTS // (DP_SIZE + 1), (
                f"requests are imbalanced: {stats_loggers}"
            )