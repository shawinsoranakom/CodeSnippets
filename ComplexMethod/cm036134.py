def run_tests(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    test_configs: list[tuple],
    test_sampling_params: list[dict[str, Any]],
):
    """Test consistency of combos of async scheduling, preemption,
    uni/multiproc executor with spec decoding."""

    # Flex attention supports float32.
    attention_config = {"backend": "FLEX_ATTENTION"}

    with monkeypatch.context() as m:
        # lock matmul precision to full FP32 (IEEE)
        m.setenv("VLLM_FLOAT32_MATMUL_PRECISION", "highest")
        outputs: list[tuple[str, list, list]] = []
        for n, (
            test_preemption,
            executor,
            async_scheduling,
            spec_config,
            test_prefill_chunking,
        ) in enumerate(test_configs, 1):
            test_str = f"{n}/{len(test_configs)}"
            test_results = run_test(
                model,
                test_str,
                test_sampling_params,
                test_preemption,
                executor,
                async_scheduling,
                spec_config,
                test_prefill_chunking=test_prefill_chunking,
                attention_config=attention_config,
            )
            outputs.append(test_results)

    baseline_config, baseline_tests, _ = outputs[0]
    _, _, baseline_acceptances = next(
        (o for o in outputs if o[2] is not None), (None, None, None)
    )

    print(f"BASELINE: config=[{baseline_config}], accept_rates={baseline_acceptances}")

    failure = None
    for test_config, test_outputs, test_acceptance_rates in outputs[1:]:
        for (base_outs, base_logprobs), base_acceptance_rate, (
            test_outs,
            test_logprobs,
        ), test_acceptance_rate, params in zip(
            baseline_tests,
            baseline_acceptances or repeat(None),
            test_outputs,
            test_acceptance_rates or repeat(None),
            test_sampling_params,
        ):
            reason = None
            try:
                check_outputs_equal(
                    outputs_0_lst=base_outs,
                    outputs_1_lst=test_outs,
                    name_0=f"baseline=[{baseline_config}], params={params}",
                    name_1=f"config=[{test_config}], params={params}",
                )
            except AssertionError as e:
                reason = "outputs ", e

            if reason is None:
                try:
                    assert _all_logprobs_match(base_logprobs, test_logprobs)
                except AssertionError as e:
                    reason = "logprobs", e

            if reason is None:
                try:
                    if (
                        base_acceptance_rate is not None
                        and test_acceptance_rate is not None
                    ):
                        if "spec_mml=None" in test_config:
                            # Preemption causes more variance in acceptance rates
                            if (
                                current_platform.is_rocm()
                                and "preemption=True" in test_config
                            ):
                                tolerance = 0.10
                            else:
                                tolerance = 0.05
                            assert (
                                test_acceptance_rate > base_acceptance_rate
                                or test_acceptance_rate
                                == pytest.approx(base_acceptance_rate, rel=tolerance)
                            )
                        else:
                            # Currently the reported acceptance rate is expected to be
                            # lower when we sometimes skip drafting altogether.
                            assert test_acceptance_rate > 0.1
                except AssertionError as e:
                    reason = "accept  ", e

            if reason is None:
                print(
                    f"\033[32mPASSED\033[0m:           "
                    f"config=[{test_config}], params={params}"
                    f" accept_rate={test_acceptance_rate}"
                )
            else:
                reason_str, _ = reason
                print(
                    f"\033[31mFAILED\033[0m({reason_str}): "
                    f"config=[{test_config}], params={params}"
                    f" accept_rate={test_acceptance_rate}"
                )
                if failure is None:
                    _, failure = reason

    if failure is not None:
        raise failure