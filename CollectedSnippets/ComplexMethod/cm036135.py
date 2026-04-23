def run_test(
    model: str,
    test_str: str,
    sampling_param_tests: list[dict[str, Any]],
    test_preemption: bool,
    executor: str,
    async_scheduling: bool,
    spec_config: dict[str, Any] | None,
    test_prefill_chunking: bool,
    attention_config: dict[str, Any] | None = None,
):
    spec_decoding = spec_config is not None
    cache_arg: dict[str, Any] = (
        # Force preemptions
        dict(num_gpu_blocks_override=32)
        if test_preemption
        else dict(gpu_memory_utilization=0.9)
    )
    spec_mml = (spec_config or {}).get("max_model_len")
    spec_method = (spec_config or {}).get("method", "none")
    test_config = (
        f"executor={executor}, preemption={test_preemption}, "
        f"async_sched={async_scheduling}, "
        f"chunk_prefill={test_prefill_chunking}, "
        f"spec_decoding={spec_decoding}, spec_method={spec_method}, spec_mml={spec_mml}"
    )
    print("-" * 80)
    print(f"---- TESTING {test_str}: {test_config}")
    print("-" * 80)

    with VllmRunner(
        model,
        max_model_len=4096,
        enable_chunked_prefill=test_prefill_chunking,
        # Force prefill chunking
        max_num_batched_tokens=48 if test_prefill_chunking else None,
        enforce_eager=ENFORCE_EAGER,
        async_scheduling=async_scheduling,
        distributed_executor_backend=executor,
        dtype="float32",
        speculative_config=spec_config,
        disable_log_stats=False,
        attention_config=attention_config,
        enable_prefix_caching=False if current_platform.is_rocm() else None,
        **cache_arg,
    ) as vllm_model:
        results = []
        acceptance_rates: list[float] | None = [] if spec_decoding else None
        for override_params in sampling_param_tests:
            metrics_before = vllm_model.llm.get_metrics()
            print(f"----------- RUNNING PARAMS: {override_params}")
            results.append(
                vllm_model.generate(
                    example_prompts,
                    sampling_params=SamplingParams(**default_params, **override_params),
                    return_logprobs=True,
                )
            )
            metrics_after = vllm_model.llm.get_metrics()
            if acceptance_rates is not None:
                acceptance_rate = _get_acceptance_rate(metrics_before, metrics_after)
                acceptance_rates.append(acceptance_rate)
                print(f"ACCEPTANCE RATE {acceptance_rate}")

            if test_preemption:
                preemptions = _get_count(
                    metrics_before, metrics_after, "vllm:num_preemptions"
                )
                assert preemptions > 0, "preemption test had no preemptions"

    if len(results) > 1:
        # First check that the different parameter configs
        # actually result in different output.
        for (other_test_outs, other_test_logprobs), params in zip(
            results[1:], sampling_param_tests[1:]
        ):
            with pytest.raises(AssertionError):
                check_outputs_equal(
                    outputs_0_lst=results[0][0],
                    outputs_1_lst=other_test_outs,
                    name_0=f"baseline params={params}",
                    name_1=f"other params={params}",
                )
                assert _all_logprobs_match(results[0][1], other_test_logprobs)

    return test_config, results, acceptance_rates