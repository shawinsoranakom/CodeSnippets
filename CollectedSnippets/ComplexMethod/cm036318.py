async def test_pause_abort():
    """Test that mode='abort' aborts in-flight requests immediately."""
    with ExitStack() as after:
        with set_default_torch_num_threads(1):
            engine = AsyncLLM.from_engine_args(TEXT_ENGINE_ARGS)
        after.callback(engine.shutdown)

        # Start a long-running request
        sampling_params = SamplingParams(max_tokens=1000, ignore_eos=True)
        outputs: list[RequestOutput] = []

        async def gen():
            async for out in engine.generate(
                request_id="test-abort-pause",
                prompt=TEXT_PROMPT,
                sampling_params=sampling_params,
            ):
                outputs.append(out)
            return outputs[-1] if outputs else None

        # Start generation task
        gen_task = asyncio.create_task(gen())

        # Wait for some tokens to be generated
        while len(outputs) < 3:
            await asyncio.sleep(0.01)

        # Pause with abort mode
        await engine.pause_generation(mode="abort")

        # Wait for task to complete (should be aborted)
        final_output = await gen_task

        # Request should be finished (aborted)
        assert final_output is not None
        assert final_output.finished
        assert final_output.outputs[0].finish_reason == "abort"

        # Also test that new requests are blocked while paused, then resume
        assert await engine.is_paused()

        request_completed = False

        async def gen_blocked():
            nonlocal request_completed
            async for out in engine.generate(
                request_id="test-blocked",
                prompt=TEXT_PROMPT,
                sampling_params=SamplingParams(max_tokens=5),
            ):
                pass
            request_completed = True
            return out

        # Start a request (should block)
        gen_task2 = asyncio.create_task(gen_blocked())

        # Wait a bit - request should not have completed
        await asyncio.sleep(0.3)
        assert not request_completed, "Request should be blocked while paused"

        # Resume
        await engine.resume_generation()

        # Now request should complete
        final_output2 = await asyncio.wait_for(gen_task2, timeout=10.0)
        assert request_completed
        assert final_output2.finished