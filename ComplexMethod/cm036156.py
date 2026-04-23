def test_spec_decode_logprobs(
    logprobs_mode: LogprobsMode,
    model_setup: tuple[str, str, dict, int],
    monkeypatch,
):
    """Spec decode logprobs should match those of the base model.

    Runs the base model and spec decode model sequentially, ensuring
    only one LLM instance is alive at a time to avoid GPU memory
    contention. Both use identical chunked prefill settings and eager
    mode to control for infrastructure differences.

    Args:
        logprobs_mode: logprobs mode.
        model_setup: Tuple of (method, base model name,
            speculative_config dict, top_logprobs).
        monkeypatch: pytest fixture for setting env vars.
    """
    from vllm import LLM

    # The ROCm skinny GEMM kernels (gemm_kernels.cu) are
    # non-deterministic across LLM instantiations due to persistent
    # workgroup scheduling and wave-level shuffle reductions, which
    # causes logprob differences that get misattributed to spec decode.
    # Disable them so this test isolates spec decode correctness only.
    # TODO(akaratza): Remove this workaround once the follow-up to
    # https://github.com/vllm-project/vllm/pull/33493#issuecomment-3906083975
    # lands with a determinism fix for wvSplitK kernels.
    monkeypatch.setenv("VLLM_ROCM_USE_SKINNY_GEMM", "0")

    method, model_name, spec_config, top_logprobs = model_setup

    prompt = "Hello world " * 50
    sampling_params = SamplingParams(
        temperature=0, logprobs=top_logprobs, max_tokens=10, ignore_eos=False
    )
    penalty_sampling_params = SamplingParams(
        temperature=0,
        logprobs=top_logprobs,
        max_tokens=10,
        ignore_eos=False,
        presence_penalty=-1.0,
    )

    max_model_len = 256

    # Run base LLM.
    ref_llm = LLM(
        model=model_name,
        max_logprobs=5,
        max_model_len=max_model_len,
        seed=42,
        logprobs_mode=logprobs_mode,
        gpu_memory_utilization=0.4,
        enable_prefix_caching=False,
        **ROCM_DETERMINISM_KWARGS,
    )
    ref_results = ref_llm.generate(
        [prompt, prompt], [sampling_params, penalty_sampling_params]
    )
    # Collect logprobs outputs from reference LLM.
    ref_logprobs = []
    for results in ref_results:
        for output in results.outputs:
            for logprobs in output.logprobs:
                ref_logprobs.extend(logprobs.values())
    del ref_llm
    torch.accelerator.empty_cache()
    cleanup_dist_env_and_memory()

    # Run spec decode LLM.
    # Add max_model_len to spec_config if not present
    spec_config_with_len = {**spec_config, "max_model_len": max_model_len}
    spec_llm = LLM(
        model_name,
        speculative_config=spec_config_with_len,
        max_logprobs=5,
        max_model_len=max_model_len,
        seed=42,
        logprobs_mode=logprobs_mode,
        gpu_memory_utilization=0.4,
        # Force prefill chunking
        enable_chunked_prefill=True,
        max_num_batched_tokens=32,
        enable_prefix_caching=False,
        **ROCM_DETERMINISM_KWARGS,
    )
    spec_results = spec_llm.generate(
        [prompt, prompt], [sampling_params, penalty_sampling_params]
    )
    # Collect logprobs outputs from spec decode LLM.
    spec_logprobs = []
    for results in spec_results:
        for output in results.outputs:
            for logprobs in output.logprobs:
                spec_logprobs.extend(logprobs.values())
    del spec_llm
    torch.accelerator.empty_cache()
    cleanup_dist_env_and_memory()

    # Per-token logprobs are expected to be the same.
    assert len(ref_logprobs) == len(spec_logprobs)
    for ref_logprob, spec_logprob in zip(ref_logprobs, spec_logprobs):
        assert math.isclose(
            ref_logprob.logprob, spec_logprob.logprob, rel_tol=5e-2, abs_tol=1e-1
        ), (
            f"Logprob mismatch: ref={ref_logprob.logprob} "
            f"spec={spec_logprob.logprob} "
            f"diff={abs(ref_logprob.logprob - spec_logprob.logprob)} "
            f"(token={ref_logprob.decoded_token!r})"
        )
        assert ref_logprob.rank == spec_logprob.rank, (
            f"Rank mismatch: ref={ref_logprob.rank} "
            f"spec={spec_logprob.rank} "
            f"(token={ref_logprob.decoded_token!r})"
        )
        assert ref_logprob.decoded_token == spec_logprob.decoded_token