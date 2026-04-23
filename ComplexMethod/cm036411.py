def test_spec_decode_acceptance_length():
    """Validate PD+SD acceptance length against standalone baseline.

    Sends MT-Bench prompts through the PD proxy (completions API),
    then checks that the decode server's speculative decoding metrics
    match the known standalone baselines.
    """
    config = _get_model_config()
    rtol = config.rtol if config.rtol is not None else DEFAULT_RTOL

    prompts = _get_mt_bench_prompts()
    assert len(prompts) == DEFAULT_NUM_PROMPTS, (
        f"Expected {DEFAULT_NUM_PROMPTS} prompts, got {len(prompts)}"
    )

    client = openai.OpenAI(api_key="EMPTY", base_url=PROXY_BASE_URL)
    for i, prompt in enumerate(prompts):
        resp = client.completions.create(
            model=MODEL_NAME,
            prompt=prompt,
            max_tokens=DEFAULT_OUTPUT_LEN,
            temperature=0.0,
            top_p=1.0,
        )
        if i < 3:
            text = resp.choices[0].text.strip()[:100]
            print(f"  [{i}] {prompt[:60]}... -> {text}...")

    # ── Extract metrics from decode server ────────────────────────────
    n_drafts = _fetch_metric("vllm:spec_decode_num_drafts_total")
    n_accepted = _fetch_metric("vllm:spec_decode_num_accepted_tokens_total")

    assert n_drafts > 0, "No spec-decode drafts were generated"

    acceptance_length = 1 + (n_accepted / n_drafts)

    per_pos_counts = _fetch_per_position_acceptance()
    per_pos_rates = [
        per_pos_counts.get(i, 0) / n_drafts
        for i in range(len(config.expected_acceptance_lengths_per_pos))
    ]

    # ── Report ────────────────────────────────────────────────────────
    expected = config.expected_acceptance_length
    expected_per_pos = config.expected_acceptance_lengths_per_pos

    print(
        f"\n{config.id}: acceptance_length={acceptance_length:.3f} "
        f"(expected={expected:.3f})"
    )
    print(f"  Drafts: {n_drafts:.0f}, Accepted: {n_accepted:.0f}")
    for i, (actual, exp) in enumerate(zip(per_pos_rates, expected_per_pos)):
        print(f"  Position {i}: {actual:.4f} (expected: {exp:.4f})")

    # ── Assert overall acceptance length ──────────────────────────────
    rel_error = abs(acceptance_length - expected) / expected

    assert rel_error <= rtol, (
        f"Acceptance length regression for {config.id}! "
        f"Expected: {expected:.3f}, "
        f"Got: {acceptance_length:.3f}, "
        f"Relative error: {rel_error:.2%} (tolerance: {rtol:.0%}). "
        f"This may indicate drafter KV was not correctly transferred."
    )

    # ── Assert per-position acceptance ────────────────────────────────
    for i, (actual, exp) in enumerate(zip(per_pos_rates, expected_per_pos)):
        if exp > 0:
            pos_err = abs(actual - exp) / exp
            assert pos_err <= rtol, (
                f"Per-position acceptance regression at position {i} "
                f"for {config.id}! "
                f"Expected: {exp:.4f}, Got: {actual:.4f}, "
                f"Relative error: {pos_err:.2%} "
                f"(tolerance: {rtol:.0%})"
            )

    print(
        f"\n=== PASS: {config.id} acceptance length {acceptance_length:.3f} "
        f"within {rtol:.0%} of {expected:.3f} ==="
    )