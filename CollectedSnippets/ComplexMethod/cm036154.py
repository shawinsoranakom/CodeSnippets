def test_all_logprobs(example_prompts):
    """Engine should return all vocabulary logprobs and prompt logprobs

    Args:
      example_prompts: list of example prompts (test fixture)
    """
    with VllmRunner(
        "facebook/opt-125m",
        max_logprobs=-1,
        enable_prefix_caching=False,
        gpu_memory_utilization=0.15,
        max_model_len=256,
    ) as runner:
        sampling_params_logprobs_all = SamplingParams(
            max_tokens=5, logprobs=-1, prompt_logprobs=-1
        )
        results_logprobs_all = runner.llm.generate(
            example_prompts, sampling_params=sampling_params_logprobs_all
        )
        vocab_size = runner.llm.llm_engine.model_config.get_vocab_size()

        for i in range(len(results_logprobs_all)):
            logprobs = results_logprobs_all[i].outputs[0].logprobs
            prompt_logprobs = results_logprobs_all[i].prompt_logprobs
            assert logprobs is not None
            for logprob in logprobs:
                assert len(logprob) == vocab_size
            assert prompt_logprobs is not None
            assert prompt_logprobs[0] is None
            for prompt_logprob in prompt_logprobs[1:]:
                assert len(prompt_logprob) == vocab_size