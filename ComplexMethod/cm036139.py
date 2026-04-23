def test_min_tokens_eos_behavior(llm_v1: LLM):
    """
    Verify EOS handling with and without min_tokens.

    - Without min_tokens: expect early EOS -> finish_reason == "stop",
      stop_reason is None, and generated tokens < max_tokens (25).
    - With min_tokens: EOS should be blocked until min_tokens is reached
      (finish_reason == "length"); verify that eos_token_id does not appear
      in generated token_ids.
    """
    # tokenizer + eos id
    tokenizer = llm_v1.get_tokenizer()
    eos_token_id = tokenizer.eos_token_id

    prompt = "Give a file extension."
    max_toks = 32

    # Case 1: WITHOUT min_tokens
    sp_no_min = SamplingParams(
        max_tokens=max_toks,
        temperature=GREEDY,
    )
    out_no_min = llm_v1.generate([prompt], sp_no_min)
    assert len(out_no_min) == 1
    choice_no_min = out_no_min[0].outputs[0]

    ids_no_min = choice_no_min.token_ids or []
    finish_no_min = choice_no_min.finish_reason
    stop_no_min = choice_no_min.stop_reason

    print(
        "[no-min] tokens=",
        len(ids_no_min),
        " finish=",
        finish_no_min,
        " stop_reason=",
        stop_no_min,
    )

    assert finish_no_min == "stop", (
        f"Expected finish_reason 'stop' without min_tokens, got {finish_no_min}"
    )
    assert stop_no_min is None, (
        "For EOS-based stop (no user stop strings), stop_reason should be None."
    )
    assert len(ids_no_min) < max_toks, (
        f"Expected early EOS with < {max_toks} tokens, got {len(ids_no_min)}"
    )

    # Case 2: WITH min_tokens
    sp_with_min = SamplingParams(
        min_tokens=max_toks,
        max_tokens=max_toks,
        temperature=GREEDY,
    )
    out_with_min = llm_v1.generate([prompt], sp_with_min)
    assert len(out_with_min) == 1
    choice_with_min = out_with_min[0].outputs[0]

    ids_with_min = choice_with_min.token_ids or []
    finish_with_min = choice_with_min.finish_reason
    stop_with_min = choice_with_min.stop_reason

    print(
        "[with-min] tokens=",
        len(ids_with_min),
        " finish=",
        finish_with_min,
        " stop_reason=",
        stop_with_min,
    )

    # Exact length reached; EOS should have been blocked
    assert len(ids_with_min) == max_toks, (
        f"Expected exactly {max_toks} tokens with min_tokens; got {len(ids_with_min)}"
    )
    assert finish_with_min == "length", (
        f"Expected finish_reason 'length'; got {finish_with_min}"
    )
    assert eos_token_id not in ids_with_min, (
        "EOS token id should not appear when min_tokens prevents early EOS."
    )