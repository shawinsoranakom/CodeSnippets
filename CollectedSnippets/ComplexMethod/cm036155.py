def test_logprobs_mode(logprobs_mode: LogprobsMode):
    """Test with LLM engine with different logprobs_mode.
    For logprobs, we should have non-positive values.
    For logits, we should expect at least one positive values.
    """
    from vllm import LLM

    llm = LLM(
        "facebook/opt-125m",
        max_logprobs=5,
        enable_prefix_caching=False,
        # 2 other llms alive during whole session
        gpu_memory_utilization=0.05,
        max_model_len=16,
        logprobs_mode=logprobs_mode,
    )
    try:
        vllm_sampling_params = SamplingParams(logprobs=1)
        results = llm.generate(["Hello world"], sampling_params=vllm_sampling_params)

        total_token_with_logprobs = 0
        positive_values = 0
        for output in results[0].outputs:
            for logprobs in output.logprobs:
                for token_id in logprobs:
                    logprob = logprobs[token_id]
                    if logprobs_mode in ("raw_logprobs", "processed_logprobs"):
                        assert logprob.logprob <= 0
                    if logprob.logprob > 0:
                        positive_values = positive_values + 1
                    total_token_with_logprobs = total_token_with_logprobs + 1
        assert total_token_with_logprobs >= len(results[0].outputs)
        if logprobs_mode in ("raw_logits", "processed_logits"):
            assert positive_values > 0
    finally:
        del llm
        torch.accelerator.empty_cache()
        cleanup_dist_env_and_memory()