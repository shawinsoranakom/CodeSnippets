def test_moe_startup(monkeypatch, vllm_runner, fresh_vllm_cache, mega_aot_artifact):
    monkeypatch.setenv("VLLM_ENABLE_V1_MULTIPROCESSING", "0")
    monkeypatch.setenv("VLLM_USE_MEGA_AOT_ARTIFACT", mega_aot_artifact)

    # Cold start in a forked child (must fork before CUDA init).
    # This model has 32 identical transformer layers which produce
    # 33 subgraphs after splitting on attention — only 3 are unique.
    ctx = mp.get_context("fork")
    p = ctx.Process(target=_cold_start, args=(vllm_runner,))
    p.start()
    p.join()
    assert p.exitcode == 0, "Cold-start child failed"

    # Warm start — compiled artifacts loaded from disk cache.
    counters.clear()
    with compilation_counter.expect(
        num_compiled_artifacts_loaded=3,
        num_compiled_artifacts_saved=0,
    ):
        _run_vllm(vllm_runner)
    mega_aot_active = envs.VLLM_USE_MEGA_AOT_ARTIFACT and is_torch_equal_or_newer(
        "2.10.0"
    )
    if mega_aot_active:
        # MEGA_AOT_ARTIFACT is enabled, so we expect no aot_autograd running on
        # subgraphs.
        assert counters["aot_autograd"]["total"] == 0
    else:
        assert counters["aot_autograd"]["total"] == 30
    assert counters["aot_autograd"]["autograd_cache_miss"] == 0
    assert (
        counters["aot_autograd"]["autograd_cache_hit"] == 0
    )