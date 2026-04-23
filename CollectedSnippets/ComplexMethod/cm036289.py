def test_delayed_start_and_max_iters(default_profiler_config):
    """Test combined delayed start and max iterations."""
    default_profiler_config.delay_iterations = 2
    default_profiler_config.max_iterations = 2
    profiler = ConcreteWorkerProfiler(default_profiler_config)
    profiler.start()

    # Step 1
    profiler.step()
    assert profiler._running is False
    assert profiler._active is True

    # Step 2 (Starts now)
    profiler.step()
    assert profiler._profiling_for_iters == 1
    assert profiler._running is True
    assert profiler._active is True

    # Next iteration
    profiler.step()
    assert profiler._profiling_for_iters == 2
    assert profiler._running is True

    # Iteration 2 (exceeds max)
    profiler.step()

    # Should have stopped now
    assert profiler._running is False
    assert profiler.stop_call_count == 1