def test_mamba_n1_p_side_truncation():
    """P-side: Mamba truncates prompt to N-1, sets max_tokens=1.

    Also verifies idempotency (calling again is a no-op) which is
    needed for preemption safety via the _p_side_truncated guard,
    and that non-Mamba models skip truncation entirely.
    """
    sched = make_nixl_scheduler(has_mamba=True, is_hma_required=True)
    req = create_request(num_tokens=10, do_remote_decode=True)
    req.max_tokens = 128
    original_len = len(req.prompt_token_ids)

    count, is_async = sched.get_num_new_matched_tokens(req, num_computed_tokens=0)

    assert count == 0
    assert is_async is False
    assert len(req.prompt_token_ids) == original_len - 1
    assert req.num_prompt_tokens == original_len - 1
    assert req.max_tokens == 1
    assert req.kv_transfer_params["_p_side_truncated"] is True

    # Idempotency: second call must not truncate further
    sched.get_num_new_matched_tokens(req, num_computed_tokens=0)
    assert len(req.prompt_token_ids) == original_len - 1

    # Non-Mamba: truncation is skipped
    fa_sched = make_nixl_scheduler(has_mamba=False, is_hma_required=False)
    fa_req = create_request(num_tokens=10, do_remote_decode=True)
    fa_original = len(fa_req.prompt_token_ids)

    fa_sched.get_num_new_matched_tokens(fa_req, num_computed_tokens=0)
    assert len(fa_req.prompt_token_ids) == fa_original