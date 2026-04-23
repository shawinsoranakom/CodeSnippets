def test_partition_wrapper_applied_on_aot_load(
    monkeypatch: pytest.MonkeyPatch, vllm_tmp_cache: Path, mocker
):
    """
    Test that partition wrappers are applied when loading AOT cached functions.

    This test verifies the fix for GitHub issue #31439 where AOT compile
    caused 2x latency regression when use_inductor_graph_partition=True.
    The root cause was that partition wrapper context was bypassed when
    loading from AOT cache.
    """
    from vllm.config import CUDAGraphMode

    args = (torch.randn(10, 10),)
    monkeypatch.setenv("VLLM_USE_AOT_COMPILE", "1")

    # Create config with partition enabled
    vllm_config = VllmConfig(
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            use_inductor_graph_partition=True,
            cudagraph_mode=CUDAGraphMode.PIECEWISE,
        )
    )

    # First compilation - save to cache
    with use_vllm_config(vllm_config):
        compiled_mod = CompiledMod(vllm_config=vllm_config)
        compiled_mod(*args)

    disable_envs_cache()

    # Second run - load from cache, verify partition wrapper applied
    monkeypatch.setenv("VLLM_FORCE_AOT_LOAD", "1")
    vllm_config = VllmConfig(
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            use_inductor_graph_partition=True,
            cudagraph_mode=CUDAGraphMode.PIECEWISE,
        )
    )

    # Use mocker to spy on set_customized_partition_wrappers
    spy = mocker.spy(torch._inductor.utils, "set_customized_partition_wrappers")

    with use_vllm_config(vllm_config):
        compiled_mod = CompiledMod(vllm_config=vllm_config)

        # First call after restart: loads from AOT cache.
        # This tests the fix for the first call after a restart.
        compiled_mod(*args)

        # Verify cache was loaded
        assert compiled_mod.was_aot_compile_fn_loaded_from_disk, (
            "Expected was_aot_compile_fn_loaded_from_disk to be True"
        )

        # Verify partition wrapper was called on AOT load.
        assert spy.call_count >= 2, (
            "Expected partition wrapper to be set and cleared on AOT load, "
            f"got {spy.call_count} calls"
        )
        # First call should set a wrapper, last call should clear it
        assert spy.call_args_list[0][0][0] is not None, (
            "First call on AOT load should set a wrapper function"
        )
        assert spy.call_args_list[-1][0][0] is None, (
            "Last call on AOT load should clear the wrapper"
        )

        # Reset for the next check.
        spy.reset_mock()

        # Subsequent call: uses the cached `aot_compiled_fn`.
        # This tests the fix for subsequent calls.
        compiled_mod(*args)

        # Verify partition wrapper was called on the subsequent call.
        assert spy.call_count >= 2, (
            "Expected partition wrapper set and cleared on subsequent "
            f"call, got {spy.call_count} calls"
        )
        assert spy.call_args_list[0][0][0] is not None, (
            "First call on subsequent call should set a wrapper function"
        )
        assert spy.call_args_list[-1][0][0] is None, (
            "Last call on subsequent call should clear the wrapper"
        )