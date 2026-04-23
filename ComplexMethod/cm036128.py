def test_logprobs_without_batch_invariance_should_fail(
    backend, monkeypatch: pytest.MonkeyPatch
):
    """
    This test is the inverse of test_logprobs_bitwise_batch_invariance_bs1_vs_bsN.
    It DISABLES batch invariance mode and expects to see non-deterministic behavior
    between BS=1 and BS=N runs. This demonstrates that batch invariance is actually
    doing something useful.

    The test will PASS if we detect differences (proving batch invariance matters).
    The test will FAIL if everything matches (suggesting batch invariance isn't needed).
    """
    # CRITICAL: Disable batch invariance for this test
    monkeypatch.setenv("VLLM_BATCH_INVARIANT", "0")
    monkeypatch.setattr(envs, "VLLM_BATCH_INVARIANT", False)
    seed = int(os.getenv("VLLM_TEST_SEED", "12345"))
    random.seed(seed)
    tp_size = int(os.getenv("VLLM_TEST_TP_SIZE", "1"))

    print(f"\n{'=' * 80}")
    print("BATCH INVARIANCE DISABLED: Expecting non-deterministic behavior")
    print(f"{'=' * 80}\n")

    llm = LLM(
        model=TEST_MODEL,
        tensor_parallel_size=tp_size,
        max_num_seqs=32,
        max_model_len=8192,
        dtype="auto",
        enforce_eager=IS_DEVICE_CAPABILITY_BELOW_90,
        attention_config={"backend": backend},
    )

    # build ragged prompts to change shapes significantly across BS=1 vs BS=N
    long_min = int(os.getenv("VLLM_MIN_PROMPT", "768"))
    long_max = int(os.getenv("VLLM_MAX_PROMPT", "2048"))
    prompts: list[str] = []
    options = [
        (max(long_min, 1536), max(long_max, 3072)),  # very long
        (max(1024, long_min), max(2048, long_max)),  # long
        (256, 512),  # mid
        (10, 20),  # short
    ]

    for _ in range(32):
        lo, hi = random.choice(options)
        prompts.append(_random_prompt(lo, hi))

    sp = SamplingParams(
        temperature=0.6,
        top_p=1.0,
        max_tokens=8,
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

    # BS=N: run prompts in a batch and collect logprobs per step for each prompt.
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
    differences_found = []
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
            differences_found.append(
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
            differences_found.append(
                {
                    "prompt_idx": i,
                    "step": "sampling",
                    "reason": "Different tokens sampled",
                    "prompt_preview": prompts[i][:100],
                    "bs1_tokens": tokens_bs1,
                    "bsN_tokens": tokens_bsN,
                }
            )
            continue

        for t, (a, b) in enumerate(zip(logprobs_bs1, logprobs_bsN)):
            if a.shape != b.shape:
                differences_found.append(
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
                print(
                    f"\n[EXPECTED DIVERGENCE FOUND] Prompt {i}, "
                    f"Token {t}: max_diff={max_diff:.6e}"
                )
                bs1_tok = tokens_bs1[t] if t < len(tokens_bs1) else "N/A"
                bsN_tok = tokens_bsN[t] if t < len(tokens_bsN) else "N/A"
                print(f"  Token IDs: bs1={bs1_tok}, bsN={bsN_tok}")
                print(f"  BS=1 logprob: {a.tolist()}")
                print(f"  BS=N logprob: {b.tolist()}")
                differences_found.append(
                    {
                        "prompt_idx": i,
                        "step": t,
                        "reason": f"Bitwise mismatch (max_diff={max_diff:.6e})",
                        "prompt_preview": prompts[i][:100],
                        "bs1_tokens": tokens_bs1,
                        "bsN_tokens": tokens_bsN,
                    }
                )
                break

    # Print summary
    print(f"\n{'=' * 80}")
    if differences_found:
        success_msg = (
            f"✓ SUCCESS: Batch invariance is doing something! "
            f"Found {len(differences_found)}/{len(prompts)} prompts "
            f"with differences when batch invariance was DISABLED."
        )
        print(success_msg)
        print(f"{'=' * 80}")
        for diff in differences_found:
            print(f"\nPrompt {diff['prompt_idx']} (step {diff['step']}):")
            print(f"  Reason: {diff['reason']}")
            print(f"  Preview: {diff['prompt_preview']}...")
            if "bs1_tokens" in diff:
                print(f"  BS=1 tokens: {diff['bs1_tokens']}")
            if "bsN_tokens" in diff:
                print(f"  BS=N tokens: {diff['bsN_tokens']}")
        print(f"{'=' * 80}\n")
        # Test PASSES because we found differences (batch invariance matters!)
        return
    else:
        # Test FAILS because everything matched even without batch invariance
        fail_msg = (
            f"✗ UNEXPECTED: All {len(prompts)} prompts matched "
            f"between BS=1 and BS=N even with batch invariance DISABLED. "
            f"This suggests batch invariance might not be necessary, "
            f"or the test needs more sensitive prompts."
        )
        print(fail_msg)
        print(f"{'=' * 80}\n")
        pytest.fail(fail_msg)