def test_logprobs_bitwise_batch_invariance_bs1_vs_bsN(
    backend,
):
    seed = int(os.getenv("VLLM_TEST_SEED", "12345"))
    random.seed(seed)
    tp_size = int(os.getenv("VLLM_TEST_TP_SIZE", "1"))

    # For batch invariance, disable custom all-reduce to ensure deterministic
    # all-reduce operations (custom all-reduce may not be deterministic)
    import vllm.envs as envs

    disable_custom_ar = envs.VLLM_BATCH_INVARIANT

    if disable_custom_ar:
        print(f"\n{'=' * 80}")
        print(f"BATCH INVARIANCE MODE: Disabling custom all-reduce (TP={tp_size})")
        print(f"{'=' * 80}\n")

    llm = LLM(
        model=TEST_MODEL,
        tensor_parallel_size=tp_size,
        max_num_seqs=128,
        max_model_len=8192,
        dtype="auto",  # not everything is supported
        gpu_memory_utilization=0.9,
        enforce_eager=IS_DEVICE_CAPABILITY_BELOW_90,
        attention_config={"backend": backend},
    )

    # Use more realistic prompts for better token generation
    prompts = [_random_prompt(10, 50) for _ in range(32)]

    # TODO: Update prompts to have ragged lengths in order to test chunked prefill
    #       The above tests are not currently long enough to exercise chunking.
    # prompts = (
    #     [_random_prompt(10, 50) for _ in range(28)]
    #     + [_random_prompt(256, 512) for _ in range(50)]
    #     + [_random_prompt(2048, 4096) for _ in range(50)]
    # )

    sp = SamplingParams(
        temperature=0.6,
        top_p=1.0,
        max_tokens=16,
        seed=1234,
        logprobs=5,
    )

    # BS=1: run prompts individually and collect logprobs per step.
    print("\n" + "=" * 80)
    print("STARTING BS=1 RUNS (each prompt individually)")
    print("=" * 80 + "\n")

    bs1_logprobs_per_prompt = []
    bs1_tokens_per_prompt = []
    for idx, p in enumerate(prompts):
        print(f"\n[BS=1] Running prompt {idx}/{len(prompts)} - Preview: {p[:80]}...")
        outs = llm.generate([p], sp, use_tqdm=False)
        assert len(outs) == 1
        step_logprobs, token_ids = _extract_step_logprobs(outs[0])
        if step_logprobs is None:
            pytest.skip(
                "Logits are not available on RequestOutput; "
                "enable logprobs return to run this test."
            )
        bs1_logprobs_per_prompt.append(step_logprobs)
        bs1_tokens_per_prompt.append(token_ids)
        print(f"[BS=1] Prompt {idx} generated tokens: {token_ids}")

    # BS=N: run prompts in a batch and collect logprobs per step for each
    # prompt.
    print("\n" + "=" * 80)
    print(f"STARTING BS={len(prompts)} RUN (all prompts batched)")
    print("=" * 80 + "\n")

    outs_batched = llm.generate(prompts, sp, use_tqdm=False)
    assert len(outs_batched) == len(prompts)
    bsN_logprobs_per_prompt = []
    bsN_tokens_per_prompt = []

    print(f"\n[BS={len(prompts)}] Processing batched outputs...")
    for idx, o in enumerate(outs_batched):
        tokens = o.outputs[0].token_ids if o.outputs else "N/A"
        print(f"[BS={len(prompts)}] Prompt {idx} generated tokens: {tokens}")
        step_logprobs, token_ids = _extract_step_logprobs(o)
        if step_logprobs is None:
            pytest.skip(
                "Logits are not available on RequestOutput; "
                "enable logprobs return to run this test."
            )
        bsN_logprobs_per_prompt.append(step_logprobs)
        bsN_tokens_per_prompt.append(token_ids)

    # Compare step-by-step logprobs for each prompt between BS=1 and BS=N runs.
    failed_prompts = []
    for i, (logprobs_bs1, logprobs_bsN, tokens_bs1, tokens_bsN) in enumerate(
        zip(
            bs1_logprobs_per_prompt,
            bsN_logprobs_per_prompt,
            bs1_tokens_per_prompt,
            bsN_tokens_per_prompt,
        )
    ):
        if len(logprobs_bs1) != len(logprobs_bsN):
            reason = (
                f"Different number of steps: {len(logprobs_bs1)} (BS=1) "
                f"vs {len(logprobs_bsN)} (BS=N)"
            )
            failed_prompts.append(
                {
                    "prompt_idx": i,
                    "step": "all",
                    "reason": reason,
                    "prompt_preview": prompts[i][:100],
                    "bs1_tokens": tokens_bs1,
                    "bsN_tokens": tokens_bsN,
                }
            )
            continue

        # Check if tokens match first
        if tokens_bs1 != tokens_bsN:
            failed_prompts.append(
                {
                    "prompt_idx": i,
                    "step": "sampling",
                    "reason": "Different tokens sampled",
                    "prompt_preview": prompts[i][:100],
                    "bs1_tokens": tokens_bs1,
                    "bsN_tokens": tokens_bsN,
                    "bs1_all_logprobs": [
                        logprobs_bs1[s].tolist() for s in range(len(logprobs_bs1))
                    ],
                    "bsN_all_logprobs": [
                        logprobs_bsN[s].tolist() for s in range(len(logprobs_bsN))
                    ],
                }
            )
            continue

        for t, (a, b) in enumerate(zip(logprobs_bs1, logprobs_bsN)):
            if a.shape != b.shape:
                failed_prompts.append(
                    {
                        "prompt_idx": i,
                        "step": t,
                        "reason": f"Shape mismatch: {a.shape} vs {b.shape}",
                        "prompt_preview": prompts[i][:100],
                        "bs1_tokens": tokens_bs1,
                        "bsN_tokens": tokens_bsN,
                    }
                )
                break

            if not torch.equal(a, b):
                max_diff = torch.abs(a - b).max().item()
                # Print which token failed
                print(f"\n[DIVERGENCE] Prompt {i}, Token {t}: max_diff={max_diff:.6e}")
                bs1_tok = tokens_bs1[t] if t < len(tokens_bs1) else "N/A"
                bsN_tok = tokens_bsN[t] if t < len(tokens_bsN) else "N/A"
                print(f"  Token IDs: bs1={bs1_tok}, bsN={bsN_tok}")
                print(f"  BS=1 logprob: {a.tolist()}")
                print(f"  BS=N logprob: {b.tolist()}")
                failed_prompts.append(
                    {
                        "prompt_idx": i,
                        "step": t,
                        "reason": f"Bitwise mismatch (max_diff={max_diff:.6e})",
                        "prompt_preview": prompts[i][:100],
                        "bs1_tokens": tokens_bs1,
                        "bsN_tokens": tokens_bsN,
                        "bs1_all_logprobs": [
                            logprobs_bs1[s].tolist() for s in range(len(logprobs_bs1))
                        ],
                        "bsN_all_logprobs": [
                            logprobs_bsN[s].tolist() for s in range(len(logprobs_bsN))
                        ],
                    }
                )
                break

    # Print summary of all failures
    if failed_prompts:
        print(f"\n{'=' * 80}")
        fail_msg = (
            f"BATCH INVARIANCE FAILURES: {len(failed_prompts)}/"
            f"{len(prompts)} prompts failed"
        )
        print(fail_msg)
        print(f"{'=' * 80}")
        for fail in failed_prompts:
            print(f"\nPrompt {fail['prompt_idx']} (step {fail['step']}):")
            print(f"  Reason: {fail['reason']}")
            print(f"  Preview: {fail['prompt_preview']}...")

            # Always show the tokens
            if "bs1_tokens" in fail:
                print(f"  BS=1 tokens: {fail['bs1_tokens']}")
            if "bsN_tokens" in fail:
                print(f"  BS=N tokens: {fail['bsN_tokens']}")

            if "bs1_all_logprobs" in fail:
                print(f"  BS=1 logprobs for all {len(fail['bs1_all_logprobs'])} steps:")
                for step_idx, logprobs in enumerate(fail["bs1_all_logprobs"]):
                    print(f"    Step {step_idx}: {logprobs}")
                print(f"  BS=N logprobs for all {len(fail['bsN_all_logprobs'])} steps:")
                for step_idx, logprobs in enumerate(fail["bsN_all_logprobs"]):
                    print(f"    Step {step_idx}: {logprobs}")
        print(f"{'=' * 80}\n")

        # Fail the test with summary
        msg = (
            f"Batch invariance violated in {len(failed_prompts)}/"
            f"{len(prompts)} prompts. See output above for details."
        )
        pytest.fail(msg)