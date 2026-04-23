async def test_dp_pause_abort(expert_parallel: bool):
    """Pause with abort from one client aborts in-flight requests on all DP ranks."""
    with ExitStack() as after:
        engine_args = _get_dp_pause_engine_args(expert_parallel)
        engine = AsyncLLM.from_engine_args(engine_args)
        after.callback(engine.shutdown)

        # Start several requests so they are distributed across ranks
        sampling_params = SamplingParams(max_tokens=500, ignore_eos=True)
        num_requests = 4
        outputs_by_id: dict[str, list[RequestOutput]] = {}

        async def gen(rid: str):
            out_list: list[RequestOutput] = []
            outputs_by_id[rid] = out_list
            async for out in engine.generate(
                request_id=rid,
                prompt=DP_PAUSE_PROMPT,
                sampling_params=sampling_params,
            ):
                out_list.append(out)
            return out_list[-1] if out_list else None

        tasks = [asyncio.create_task(gen(f"req-{i}")) for i in range(num_requests)]
        # Wait for some tokens on at least one request
        while not any(len(o) >= 2 for o in outputs_by_id.values()):
            await asyncio.sleep(0.02)

        await engine.pause_generation(mode="abort")

        finals = await asyncio.gather(*tasks)
        for i, final in enumerate(finals):
            assert final is not None, f"req-{i} had no output"
            assert final.finished
            assert final.outputs[0].finish_reason == "abort"

        assert await engine.is_paused()
        await engine.resume_generation()
        assert not await engine.is_paused()

        # New request completes after resume
        async for out in engine.generate(
            request_id="after-abort",
            prompt=DP_PAUSE_PROMPT,
            sampling_params=SamplingParams(max_tokens=5),
        ):
            pass
        assert out.finished
        assert not engine.output_processor.has_unfinished_requests()