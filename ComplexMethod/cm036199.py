def test_eagle3_acceptance_length(
    model_config: Eagle3ModelConfig,
    num_spec_tokens: int,
    tp_size: int,
    attention_backend: str,
    monkeypatch: pytest.MonkeyPatch,
):
    # Skip if this backend is incompatible with the model
    backend_enum = AttentionBackendEnum[attention_backend]
    if backend_enum in model_config.excluded_backends:
        pytest.skip(f"{attention_backend} is incompatible with {model_config.id}")

    with monkeypatch.context() as m:
        m.setenv("VLLM_ALLOW_INSECURE_SERIALIZATION", "1")

        with VllmRunner(
            model_name=model_config.verifier,
            speculative_config={
                "method": "eagle3",
                "model": model_config.drafter,
                "num_speculative_tokens": num_spec_tokens,
            },
            attention_config={"backend": attention_backend},
            tensor_parallel_size=tp_size,
            gpu_memory_utilization=0.7,
            disable_log_stats=False,
            max_model_len=DEFAULT_MAX_MODEL_LEN,
        ) as vllm_runner:
            tokenizer = vllm_runner.llm.get_tokenizer()
            prompt_ids = get_mt_bench_prompts(tokenizer, DEFAULT_NUM_PROMPTS)

            sampling_params = SamplingParams(
                temperature=0,
                max_tokens=DEFAULT_OUTPUT_LEN,
            )
            vllm_runner.llm.generate(
                [TokensPrompt(prompt_token_ids=ids) for ids in prompt_ids],
                sampling_params=sampling_params,
            )

            metrics = vllm_runner.llm.get_metrics()
            results = extract_acceptance_metrics(metrics, num_spec_tokens)

            actual_acceptance_length = results["acceptance_length"]
            expected = model_config.expected_acceptance_length
            actual_per_pos = results["acceptance_lengths_per_pos"]
            expected_per_pos = model_config.expected_acceptance_lengths_per_pos

            rel_error = abs(actual_acceptance_length - expected) / expected

            # Overall acceptance length always uses DEFAULT_RTOL
            assert rel_error <= DEFAULT_RTOL, (
                f"Acceptance length regression detected for {model_config.id}!\n"
                f"  Expected: {expected:.3f}\n"
                f"  Actual:   {actual_acceptance_length:.3f}\n"
                f"  Relative error: {rel_error:.2%} (tolerance: {DEFAULT_RTOL:.2%})\n"
                f"  Drafts: {results['num_drafts']}, "
                f"Accepted tokens: {results['num_accepted_tokens']}"
            )

            if expected_per_pos and len(expected_per_pos) == len(actual_per_pos):
                # Per-position checks use model-specific rtol if provided
                rtol = (
                    model_config.rtol if model_config.rtol is not None else DEFAULT_RTOL
                )
                for pos, (actual, exp) in enumerate(
                    zip(actual_per_pos, expected_per_pos)
                ):
                    if exp > 0:
                        pos_rel_error = abs(actual - exp) / exp
                        assert pos_rel_error <= rtol, (
                            f"Per-position acceptance length regression at pos {pos} "
                            f"for {model_config.id}!\n"
                            f"  Expected: {exp:.3f}\n"
                            f"  Actual:   {actual:.3f}\n"
                            f"  Relative error: {pos_rel_error:.2%} "
                            f"(tolerance: {rtol:.2%})"
                        )

            print(
                f"\n{model_config.id} [tp={tp_size}, backend={attention_backend}]: "
                f"acceptance_length={actual_acceptance_length:.3f}"
                f" (expected={expected:.3f}, rel_error={rel_error:.2%})"
            )
            print(f"  Per-position: {[f'{v:.3f}' for v in actual_per_pos]}")
            if expected_per_pos:
                print(f"  Expected:     {[f'{v:.3f}' for v in expected_per_pos]}")