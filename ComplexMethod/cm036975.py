def test_cache_load_returns_tuple_consistency_tuple_output(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that cache loading correctly handles models that return tuples.

    This verifies that when a model returns a tuple of tensors, the output
    type is preserved as a tuple between fresh compilation and cache load.
    """
    with monkeypatch.context() as m:
        args = (torch.randn(10, 10),)

        with tempfile.TemporaryDirectory() as tmpdirname:
            m.setenv("VLLM_CACHE_ROOT", tmpdirname)
            m.setenv("VLLM_USE_AOT_COMPILE", "1")
            m.setenv("VLLM_USE_MEGA_AOT_ARTIFACT", "1")
            m.setenv("VLLM_USE_STANDALONE_COMPILE", "1")
            vllm_config = make_vllm_config()

            # Fresh compilation with tuple-returning model
            with use_vllm_config(vllm_config):
                compiled_mod = CompiledModTuple(vllm_config=vllm_config)
                fresh_result = compiled_mod(*args)
                fresh_result_type = type(fresh_result)

            # Verify fresh result is a tuple
            assert isinstance(fresh_result, tuple), (
                f"Fresh compile should return tuple, got {fresh_result_type}"
            )
            assert len(fresh_result) == 2, (
                f"Fresh compile should return 2-tuple, got {len(fresh_result)}"
            )

            disable_envs_cache()

            # Load from cache
            m.setenv("VLLM_FORCE_AOT_LOAD", "1")
            vllm_config = make_vllm_config()
            with use_vllm_config(vllm_config):
                cached_mod = CompiledModTuple(vllm_config=vllm_config)
                cached_result = cached_mod(*args)
                cached_result_type = type(cached_result)

            # Verify cache was actually loaded
            assert cached_mod.was_aot_compile_fn_loaded_from_disk, (
                "Expected was_aot_compile_fn_loaded_from_disk to be True after "
                "loading from cache"
            )

            # Verify cached result is also a tuple
            assert isinstance(cached_result, tuple), (
                f"Cache load should return tuple, got {cached_result_type}. "
                "This indicates the returns_tuple logic is not preserving "
                "tuple outputs when loading from cache."
            )
            assert len(cached_result) == 2, (
                f"Cache load should return 2-tuple, got {len(cached_result)}"
            )

            # Verify values match
            assert torch.allclose(cached_result[0], fresh_result[0]), (
                "Cached result[0] values should match fresh compilation"
            )
            assert torch.allclose(cached_result[1], fresh_result[1]), (
                "Cached result[1] values should match fresh compilation"
            )