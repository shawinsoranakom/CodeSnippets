def test_suffix_decoding_acceptance(
    monkeypatch: pytest.MonkeyPatch,
    sampling_config: SamplingParams,
    model_name: str,
):
    """
    Check that suffix decoding caching takes effect and improves acceptance
    lengths and acceptance rates over multiple runs of the same prompts.
    """
    test_prompts = get_test_prompts(mm_enabled=False)

    spec_llm = LLM(
        model=model_name,
        speculative_config={
            "method": "suffix",
            "suffix_decoding_max_spec_factor": 2.0,
            "suffix_decoding_max_cached_requests": 1000,
        },
        max_model_len=1024,
        disable_log_stats=False,
    )

    # Run several times and check that the accepted tokens increase.
    num_draft = []
    num_accept = []
    for i in range(10):  # Run multiple times to warm up the cache.
        spec_llm.chat(test_prompts, sampling_config)
        # Collect draft and acceptance stats.
        metrics = spec_llm.get_metrics()
        for metric in metrics:
            if metric.name == "vllm:spec_decode_num_draft_tokens":
                num_draft.append(metric.value)
            if metric.name == "vllm:spec_decode_num_accepted_tokens":
                num_accept.append(metric.value)

    # Calculate the acceptance rates for the first and last runs.
    first_accept_tokens = num_accept[0]
    first_draft_tokens = num_draft[0]
    first_accept_rate = first_accept_tokens / first_draft_tokens

    # Take the diff since the stats are cumulative.
    last_accept_tokens = num_accept[-1] - num_accept[-2]
    last_draft_tokens = num_draft[-1] - num_draft[-2]
    last_accept_rate = last_accept_tokens / last_draft_tokens

    # Expect the acceptance length to improve.
    assert first_accept_tokens < last_accept_tokens

    # Expect the acceptance rate to improve.
    assert first_accept_rate < last_accept_rate

    # Heuristic: expect at least 80.0% acceptance rate at the end.
    assert last_accept_rate > 0.80

    del spec_llm
    torch.accelerator.empty_cache()
    cleanup_dist_env_and_memory()