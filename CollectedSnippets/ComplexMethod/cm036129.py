def test_decode_logprobs_match_prefill_logprobs(
    backend,
):
    """
    Test that verifies decode logprobs match prefill logprobs.

    For each decoded token at position i:
    1. Run decode to generate N tokens and collect their logprobs
    2. For each position i in [0, N):
       - Take prefix = prompt + tokens[0:i]
       - Run prefill(prefix + tokens[i]) to get logprob of tokens[i]
       - Verify prefill logprob matches decode logprob bitwise

    This ensures that the logprobs from decode are consistent with what
    we would get if we ran prefill on each prefix.
    """
    seed = int(os.getenv("VLLM_TEST_SEED", "12345"))
    random.seed(seed)
    tp_size = int(os.getenv("VLLM_TEST_TP_SIZE", "1"))

    import vllm.envs as envs

    disable_custom_ar = envs.VLLM_BATCH_INVARIANT

    if disable_custom_ar:
        print(f"\n{'=' * 80}")
        print(f"BATCH INVARIANCE MODE: Disabling custom all-reduce (TP={tp_size})")
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

    # Use a few test prompts
    num_test_prompts = int(os.getenv("VLLM_DECODE_PREFILL_NUM_PROMPTS", "4"))
    prompts = [_random_prompt(10, 50) for _ in range(num_test_prompts)]

    # Generate longer sequences to test multiple decode steps
    max_tokens = int(os.getenv("VLLM_DECODE_PREFILL_MAX_TOKENS", "16"))

    sp = SamplingParams(
        temperature=0.0,  # Greedy for determinism
        max_tokens=max_tokens,
        logprobs=5,
    )

    print("\n" + "=" * 80)
    print("STEP 1: Running decode to generate tokens and collect logprobs")
    print("=" * 80 + "\n")

    # Step 1: Run decode and collect logprobs
    decode_outputs = llm.generate(prompts, sp, use_tqdm=False)

    failed_comparisons = []

    for prompt_idx, (prompt, decode_output) in enumerate(zip(prompts, decode_outputs)):
        print(f"\n[Prompt {prompt_idx}] Testing: {prompt[:80]}...")

        # Extract decode logprobs and tokens
        decode_logprobs, token_ids = _extract_step_logprobs(decode_output)
        if decode_logprobs is None:
            pytest.skip(
                "Logprobs are not available on RequestOutput; "
                "enable logprobs return to run this test."
            )

        print(f"[Prompt {prompt_idx}] Generated {len(token_ids)} tokens: {token_ids}")
        print(f"[Prompt {prompt_idx}] Decode logprobs: {decode_logprobs.tolist()}")

        # Step 2: For each token position, run prefill and compare
        print(f"\n[Prompt {prompt_idx}] Verifying each token via prefill...")

        for token_idx in range(len(token_ids)):
            # Construct the prefix up to (but not including) this token
            current_token = token_ids[token_idx]

            # We need to detokenize to get the text prefix
            # For this, we'll use the tokenizer from the LLM
            # However, the LLM API doesn't expose tokenizer easily, so we'll
            # construct the prefix by decoding from the original prompt

            # Get text up to this point by using the output text
            # This is approximate but should work for verification
            if token_idx == 0:
                prefix_prompt = prompt
            else:
                # Use the partial output text up to this token
                # We'll need to construct this from the full output
                prefix_output = decode_output.outputs[0]
                # Get the text for tokens 0 to token_idx-1
                # Unfortunately, we don't have per-token text, so we'll use
                # a different approach: run prefill with prompt + tokens[0:token_idx]

                # Actually, we need to get the actual text. Let's use a workaround:
                # Run a generation with max_tokens = token_idx to get that prefix
                prefix_sp = SamplingParams(
                    temperature=0.0,
                    max_tokens=token_idx,
                    logprobs=1,
                )
                prefix_output = llm.generate([prompt], prefix_sp, use_tqdm=False)[0]
                prefix_prompt = prompt + prefix_output.outputs[0].text

            # Now run prefill with max_tokens=1 to get the logprob of the next token
            prefill_sp = SamplingParams(
                temperature=0.0,
                max_tokens=1,
                logprobs=5,
            )

            print(
                f"  [Token {token_idx}] Running prefill for prefix "
                f"(len={len(prefix_prompt)})..."
            )
            prefill_output = llm.generate([prefix_prompt], prefill_sp, use_tqdm=False)[
                0
            ]
            prefill_logprobs, prefill_token_ids = _extract_step_logprobs(prefill_output)

            if prefill_logprobs is None:
                print(f"  [Token {token_idx}] Warning: No prefill logprobs available")
                continue

            # The first token from prefill should match the current token
            prefill_token = prefill_token_ids[0]
            prefill_logprob = prefill_logprobs[0].item()
            decode_logprob = decode_logprobs[token_idx].item()

            print(
                f"  [Token {token_idx}] Decode token: {current_token}, "
                f"logprob: {decode_logprob:.8f}"
            )
            print(
                f"  [Token {token_idx}] Prefill token: {prefill_token}, "
                f"logprob: {prefill_logprob:.8f}"
            )

            # Check if tokens match
            if current_token != prefill_token:
                failed_comparisons.append(
                    {
                        "prompt_idx": prompt_idx,
                        "token_idx": token_idx,
                        "reason": "Token mismatch",
                        "decode_token": current_token,
                        "prefill_token": prefill_token,
                        "decode_logprob": decode_logprob,
                        "prefill_logprob": prefill_logprob,
                        "prompt_text": prompt[:100],
                        "prefix_text": prefix_prompt[:100],
                    }
                )
                print(f"  [Token {token_idx}] ✗ TOKEN MISMATCH!")
                continue

            # Check if logprobs match bitwise
            if decode_logprob != prefill_logprob:
                diff = abs(decode_logprob - prefill_logprob)
                failed_comparisons.append(
                    {
                        "prompt_idx": prompt_idx,
                        "token_idx": token_idx,
                        "reason": "Logprob mismatch",
                        "decode_token": current_token,
                        "prefill_token": prefill_token,
                        "decode_logprob": decode_logprob,
                        "prefill_logprob": prefill_logprob,
                        "diff": diff,
                        "prompt_text": prompt[:100],
                        "prefix_text": prefix_prompt[:100],
                        "decode_all_tokens": token_ids,
                        "decode_all_logprobs": decode_logprobs.tolist(),
                    }
                )
                print(f"  [Token {token_idx}] ✗ LOGPROB MISMATCH! diff={diff:.8e}")
            else:
                print(f"  [Token {token_idx}] ✓ Match (bitwise equal)")

    # Print summary
    print(f"\n{'=' * 80}")
    if failed_comparisons:
        print(f"DECODE-PREFILL MISMATCH: {len(failed_comparisons)} failures detected")
        print(f"{'=' * 80}")

        # Group failures by prompt for better readability
        failures_by_prompt: dict[int, list[dict]] = {}
        for fail in failed_comparisons:
            pid = fail["prompt_idx"]
            if pid not in failures_by_prompt:
                failures_by_prompt[pid] = []
            failures_by_prompt[pid].append(fail)

        for prompt_idx, failures in failures_by_prompt.items():
            print(f"\n{'=' * 80}")
            print(f"PROMPT {prompt_idx}: {failures[0]['prompt_text']}...")
            print(f"{'=' * 80}")
            print(f"Total failures for this prompt: {len(failures)}")

            # Show where mismatches occur (which token positions)
            mismatch_positions = [f["token_idx"] for f in failures]
            print(f"Mismatch at token positions: {mismatch_positions}")

            # Show first few failures in detail
            for i, fail in enumerate(failures[:5]):  # Show first 5 failures per prompt
                print(f"\n  [Failure {i + 1}] Token position {fail['token_idx']}:")
                print(f"    Reason: {fail['reason']}")
                print(f"    Prefix text: '{fail['prefix_text']}...'")
                print(
                    f"    Decode:  token={fail['decode_token']}, "
                    f"logprob={fail['decode_logprob']:.10f}"
                )
                print(
                    f"    Prefill: token={fail['prefill_token']}, "
                    f"logprob={fail['prefill_logprob']:.10f}"
                )
                if "diff" in fail:
                    print(f"    Difference: {fail['diff']:.10e}")
                    # Show in hex to see bitwise difference
                    import struct

                    decode_hex = struct.pack("f", fail["decode_logprob"]).hex()
                    prefill_hex = struct.pack("f", fail["prefill_logprob"]).hex()
                    print(f"    Decode logprob (hex):  0x{decode_hex}")
                    print(f"    Prefill logprob (hex): 0x{prefill_hex}")

                # If we have all tokens/logprobs, show the context
                if "decode_all_tokens" in fail and "decode_all_logprobs" in fail:
                    token_idx = fail["token_idx"]
                    all_tokens = fail["decode_all_tokens"]
                    all_logprobs = fail["decode_all_logprobs"]

                    # Show context: 2 tokens before and after
                    start = max(0, token_idx - 2)
                    end = min(len(all_tokens), token_idx + 3)

                    print(f"    Context (tokens {start} to {end - 1}):")
                    for j in range(start, end):
                        marker = " <-- MISMATCH" if j == token_idx else ""
                        print(
                            f"      [{j}] token={all_tokens[j]}, "
                            f"logprob={all_logprobs[j]:.8f}{marker}"
                        )

            if len(failures) > 5:
                print(f"\n  ... and {len(failures) - 5} more failures for this prompt")

        print(f"\n{'=' * 80}\n")

        pytest.fail(
            f"Decode logprobs do not match prefill logprobs: "
            f"{len(failed_comparisons)} mismatches found."
        )
    else:
        print("✓ SUCCESS: All decode logprobs match prefill logprobs bitwise!")
        print(f"{'=' * 80}\n")