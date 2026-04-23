def test_prompt_logprobs_with_chunking_and_preemption():
    """Test that prompt logprobs are correctly returned when using
    both chunked prefill and preemption.

    This test ensures that the num_prompt_logprobs tracking persists
    across preemptions and prefill chunks.
    """

    # Create prompts that will trigger chunking and preemption
    prompts = [
        "The following numbers of the sequence "
        + ", ".join(str(i) for i in range(10))
        + " are:",
        "In one word, the capital of France is ",
    ] + [f"Tell me about the number {i}: " for i in range(32)]

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=40,
        min_tokens=20,
        prompt_logprobs=2,  # Request prompt logprobs
    )

    with VllmRunner(
        "Qwen/Qwen3-0.6B",
        max_model_len=512,
        enable_chunked_prefill=True,
        max_num_batched_tokens=48,  # Force prefill chunking
        num_gpu_blocks_override=32,  # Force preemptions
        disable_log_stats=False,
        gpu_memory_utilization=0.25,
    ) as vllm_model:
        metrics_before = vllm_model.llm.get_metrics()

        # Generate with prompt logprobs using generate_w_logprobs which
        # returns (output_ids, output_str, output_logprobs, prompt_logprobs)
        outputs = vllm_model.generate_w_logprobs(
            prompts, sampling_params=sampling_params, include_prompt_token_ids=True
        )

        # Verify that all outputs have prompt logprobs
        for i, output in enumerate(outputs):
            _, _, _, prompt_token_ids, prompt_logprobs = output
            assert prompt_logprobs is not None and len(prompt_logprobs) > 0, (
                f"Output {i} missing prompt logprobs"
            )
            assert len(prompt_logprobs) == len(prompt_token_ids), (
                "Unexpected number of prompt logprob positions"
            )

            # Each position should have the requested number of logprobs
            for pos, logprobs_dict in enumerate(prompt_logprobs):
                if logprobs_dict is not None:  # First token may be None
                    assert (
                        sampling_params.prompt_logprobs
                        <= len(logprobs_dict)
                        <= sampling_params.prompt_logprobs + 1
                    ), (
                        f"Output {i} position {pos} has {len(logprobs_dict)} "
                        f"logprobs, expected {sampling_params.prompt_logprobs}"
                    )

        # Check that we actually had preemptions
        metrics_after = vllm_model.llm.get_metrics()
        preemptions_before = next(
            (m.value for m in metrics_before if m.name == "vllm:num_preemptions"), 0
        )
        preemptions_after = next(
            (m.value for m in metrics_after if m.name == "vllm:num_preemptions"), 0
        )
        preemptions = preemptions_after - preemptions_before
        assert preemptions > 0, "Test did not trigger any preemptions"

        print(f"Test passed with {preemptions} preemptions")