async def test_pause_resume_basic():
    """Test basic pause/resume flag behavior and idempotency.

    Tests:
    - pause_generation sets the paused flag
    - resume_generation clears the paused flag
    - calling pause when already paused is a no-op
    - calling resume when not paused is safe
    - all pause modes work with no requests in flight
    - rapid pause/resume cycles don't break the engine
    """
    with ExitStack() as after:
        with set_default_torch_num_threads(1):
            engine = AsyncLLM.from_engine_args(TEXT_ENGINE_ARGS)
        after.callback(engine.shutdown)

        # Initially not paused
        assert not await engine.is_paused()

        # Resume when not paused should be safe
        await engine.resume_generation()
        assert not await engine.is_paused()

        # Pause sets flag
        await engine.pause_generation(mode="abort")
        assert await engine.is_paused()

        # Pause when already paused is a no-op
        await engine.pause_generation(mode="abort")
        assert await engine.is_paused()

        # Resume clears flag
        await engine.resume_generation()
        assert not await engine.is_paused()

        # Test all modes with no requests in flight
        for mode in ("abort", "wait", "keep"):
            await engine.pause_generation(mode=mode)
            assert await engine.is_paused()
            await engine.resume_generation()
            assert not await engine.is_paused()

        # Concurrent pause/resume race conditions - should not deadlock or raise
        await asyncio.gather(
            engine.pause_generation(mode="abort"),
            engine.resume_generation(),
            engine.pause_generation(mode="abort"),
            engine.resume_generation(),
        )

        # Ensure we end in a known state
        await engine.resume_generation()
        assert not await engine.is_paused()

        # Engine should still work after all cycles
        sampling_params = SamplingParams(max_tokens=5)
        async for out in engine.generate(
            request_id="post-cycles",
            prompt=TEXT_PROMPT,
            sampling_params=sampling_params,
        ):
            pass
        assert out.finished