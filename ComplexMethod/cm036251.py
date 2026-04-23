def test_no_spec_tokens_scheduled_for_prefill_chunks():
    """Test that draft tokens are ignored for prefill chunk requests.

    When a request is being prefilled in chunks (chunked prefill), draft tokens
    from `update_draft_token_ids` should be ignored until the prefill is complete.

    The bug manifests when:
    - A prefill chunk is scheduled
    - Draft tokens are provided via update_draft_token_ids
    - The next schedule has enough budget to include spec tokens

    Without the fix, spec tokens would incorrectly be scheduled with the
    remaining prefill tokens. With the fix, draft tokens are ignored for
    prefill chunks.
    """
    num_spec_tokens = 3
    # Use budget of 50, with 80 token prompt:
    # - First chunk: 50 tokens
    # - Second chunk: 30 remaining + potentially 3 spec tokens = 33
    # Without fix: num_scheduled_spec_tokens = 33 + 50 - 80 = 3 (BUG!)
    # With fix: spec_token_ids cleared, so no spec tokens scheduled
    scheduler = create_scheduler(
        num_speculative_tokens=num_spec_tokens,
        max_num_batched_tokens=50,
        enable_chunked_prefill=True,
    )
    requests = create_requests(num_requests=1, num_tokens=80)
    req = requests[0]
    scheduler.add_request(req)

    # First schedule - prefill chunk (50 of 80 tokens)
    output = scheduler.schedule()
    assert len(output.scheduled_new_reqs) == 1
    assert output.num_scheduled_tokens[req.request_id] == 50

    # Update from output (no sampled token since still prefilling)
    req_to_index = {req.request_id: 0}
    model_runner_output = ModelRunnerOutput(
        req_ids=[req.request_id],
        req_id_to_index=req_to_index,
        sampled_token_ids=[[]],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_runner_output)

    # Provide draft tokens while request is still in prefill.
    # The fix ensures these are ignored for prefill chunks.
    draft_token_ids = DraftTokenIds([req.request_id], [[1, 2, 3]])
    scheduler.update_draft_token_ids(draft_token_ids)

    # Second schedule - remaining 30 tokens of prefill
    output = scheduler.schedule()
    # KEY ASSERTION: Should schedule exactly the remaining 30 prefill tokens,
    # NOT 33 (30 + 3 spec). Without the fix, this would be 33.
    assert output.num_scheduled_tokens[req.request_id] == 30, (
        f"Expected 30 tokens (remaining prefill only), "
        f"got {output.num_scheduled_tokens[req.request_id]}. "
        "Spec tokens should not be scheduled with prefill chunks."
    )
    # No spec tokens should be in the output
    assert req.request_id not in output.scheduled_spec_decode_tokens, (
        "Spec tokens should not be scheduled with prefill chunks"
    )

    # Update from output with a sampled token (prefill complete)
    model_runner_output = ModelRunnerOutput(
        req_ids=[req.request_id],
        req_id_to_index=req_to_index,
        sampled_token_ids=[[42]],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_runner_output)

    # Now provide draft tokens - should be accepted since prefill is complete
    draft_token_ids = DraftTokenIds([req.request_id], [[1, 2, 3]])
    scheduler.update_draft_token_ids(draft_token_ids)

    # spec_token_ids SHOULD be set after prefill is complete
    assert req.spec_token_ids == [1, 2, 3], (
        f"spec_token_ids should be set after prefill, got {req.spec_token_ids}"
    )

    # Third schedule - decode phase with spec tokens
    output = scheduler.schedule()
    # 1 new token + 3 spec tokens = 4
    assert output.num_scheduled_tokens[req.request_id] == 4
    assert req.request_id in output.scheduled_spec_decode_tokens
    assert len(output.scheduled_spec_decode_tokens[req.request_id]) == num_spec_tokens