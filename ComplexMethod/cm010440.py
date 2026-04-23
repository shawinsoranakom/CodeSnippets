def _sdpa_nested_preprocessing(query, key, value):
    # Query (Batch x Num_heads x {Q_seq_len}  x Dim_per_head)
    # Key   (Batch x Num_heads x {KV_seq_len} x Dim_per_head)
    # Value (Batch x Num_heads x {KV_seq_len} x Dim_per_head)
    q_batch_size = query.size(0)
    k_batch_size = key.size(0)
    v_batch_size = value.size(0)

    q_num_heads = query.size(1)
    k_num_heads = key.size(1)
    v_num_heads = value.size(1)

    if not (q_batch_size == k_batch_size and q_batch_size == v_batch_size) or not (
        q_num_heads == k_num_heads and k_num_heads == v_num_heads
    ):
        raise RuntimeError(
            "This path is currently not implemented for jagged layout NT."
        )
        # return _sdpa_nested_preprocessing_with_broadcast(query, key, value)

    num_heads = query.size(1)
    head_dim_qk = query.size(3)
    head_dim_v = value.size(3)
    q_t = query.transpose(1, 2)
    k_t = key.transpose(1, 2)
    v_t = value.transpose(1, 2)

    (
        cumulative_sequence_length_q,
        max_seqlen_batch_q,
        Nnz_q,
    ) = _cumulative_and_max_seq_len_nnz(q_t)
    (
        cumulative_sequence_length_kv,
        max_seqlen_batch_kv,
        Nnz_kv,
    ) = _cumulative_and_max_seq_len_nnz(k_t)

    # [TODO] K and V have to have the same Nnz, should probably torch_check
    # assume in order to not iterate over v

    # If the physical layout of the NestedTensor's storage
    # is not: batch, {seq_len}, num_heads, head_dim then we need
    # to call contiguous
    if not q_t.is_contiguous() and not _is_safe_to_get_storage_as_tensor(q_t):
        q_t = q_t.contiguous()
    if not k_t.is_contiguous() and not _is_safe_to_get_storage_as_tensor(k_t):
        k_t = k_t.contiguous()
    if not v_t.is_contiguous() and not _is_safe_to_get_storage_as_tensor(v_t):
        v_t = v_t.contiguous()

    query_buffer_reshaped = _view_as_dense(q_t, Nnz_q, num_heads, head_dim_qk)
    key_buffer_reshaped = _view_as_dense(k_t, Nnz_kv, num_heads, head_dim_qk)
    value_buffer_reshaped = _view_as_dense(v_t, Nnz_kv, num_heads, head_dim_v)

    output_nt_info = {
        "offsets": q_t.offsets(),
        "lengths": q_t.lengths(),
        "max_seqlen": q_t._get_max_seqlen(),
        "min_seqlen": q_t._get_min_seqlen(),
    }

    return (
        query_buffer_reshaped,
        key_buffer_reshaped,
        value_buffer_reshaped,
        cumulative_sequence_length_q,
        cumulative_sequence_length_kv,
        max_seqlen_batch_q,
        max_seqlen_batch_kv,
        output_nt_info,
    )