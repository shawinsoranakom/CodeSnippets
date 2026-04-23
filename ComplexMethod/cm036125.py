def test_prefill_split_across_ubatches(
    seq_lens, query_lens, split_point, expected_first_reqs, expected_second_reqs
):
    """Test splitting a prefill across ubatches"""
    import numpy as np

    device = torch.device("cpu")
    batch_spec = BatchSpec(seq_lens=seq_lens, query_lens=query_lens)
    common = create_common_attn_metadata(batch_spec, block_size=16, device=device)

    num_scheduled_tokens = np.array(query_lens, dtype=np.int32)
    qsl_np = common.query_start_loc_cpu.numpy()
    num_tokens = common.num_actual_tokens

    ubatch_slices, _ = maybe_create_ubatch_slices(
        True,
        num_scheduled_tokens,
        num_tokens,
        batch_spec.batch_size,
        split_point=split_point,
        num_ubatches=2,
    )
    assert ubatch_slices is not None and len(ubatch_slices) == 2

    first_meta = _make_metadata_with_slice(ubatch_slices[0], common)
    second_meta = _make_metadata_with_slice(ubatch_slices[1], common)

    # Token counts match the split
    assert first_meta.num_actual_tokens == split_point
    assert second_meta.num_actual_tokens == num_tokens - split_point

    # Number of requests per ubatch
    assert first_meta.num_reqs == expected_first_reqs
    assert second_meta.num_reqs == expected_second_reqs

    # Identify which request is split and how many tokens are in the first chunk
    split_req_idx = int(np.searchsorted(qsl_np, split_point, side="right") - 1)
    tokens_in_first_chunk = split_point - int(qsl_np[split_req_idx])
    orig_q_lens = common.query_start_loc_cpu[1:] - common.query_start_loc_cpu[:-1]

    # Check query length continuity: first-chunk + second-chunk == original qlen
    # First ubatch last request query length
    qlen_first_last = int(
        first_meta.query_start_loc_cpu[-1] - first_meta.query_start_loc_cpu[-2]
    )
    # Second ubatch first request query length
    qlen_second_first = int(
        second_meta.query_start_loc_cpu[1] - second_meta.query_start_loc_cpu[0]
    )
    assert qlen_first_last == tokens_in_first_chunk
    assert qlen_first_last + qlen_second_first == int(orig_q_lens[split_req_idx])

    # Check seq_lens adjustments
    # Context lengths per original request
    context_lens = [s - q for s, q in zip(seq_lens, query_lens)]

    # First ubatch: last request's seq_len should be
    #  context + tokens_in_first_chunk
    expected_seqlen = context_lens[split_req_idx] + tokens_in_first_chunk
    assert int(first_meta.seq_lens[-1]) == expected_seqlen

    # For full preceding requests in first ubatch, seq_lens should match
    #  originals
    for i in range(first_meta.num_reqs - 1):
        assert int(first_meta.seq_lens[i]) == seq_lens[i]

    # Second ubatch: first request (continuation) seq_len should be full
    #  original
    assert int(second_meta.seq_lens[0]) == seq_lens[split_req_idx]
    # Any following full requests in second ubatch should match originals
    for j in range(1, second_meta.num_reqs):
        # Map to original request index
        orig_idx = split_req_idx + j
        assert int(second_meta.seq_lens[j]) == seq_lens[orig_idx]