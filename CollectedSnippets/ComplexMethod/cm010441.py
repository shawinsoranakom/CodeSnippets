def jagged_scaled_dot_product_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_mask: torch.Tensor | None = None,
    dropout_p=0.0,
    is_causal=False,
    scale=None,
    enable_gqa=False,
):
    query, key, value, attn_mask = _autocast(query, key, value, attn_mask)
    _validate_sdpa_input(query, key, value, attn_mask, dropout_p, is_causal, scale)
    # for mypy, ugh
    if not (
        isinstance(query, NestedTensor)
        and isinstance(key, NestedTensor)
        and isinstance(value, NestedTensor)
    ):
        raise AssertionError("query, key, and value must all be NestedTensor instances")
    from torch.nested._internal.nested_tensor import (
        nested_view_from_values_offsets_lengths,
    )

    # Special path for non-ragged sequence length (e.g. for SAM where we have a ragged
    # second batch dim instead). For this case, we can just send the dense buffers through
    # vanilla SDPA.
    if query.dim() > 3 and key.dim() > 3 and value.dim() > 3 and query._ragged_idx == 1:
        output = F.scaled_dot_product_attention(
            query.values(),
            key.values(),
            value.values(),
            attn_mask=(
                attn_mask.values() if isinstance(attn_mask, NestedTensor) else attn_mask
            ),
            dropout_p=dropout_p,
            is_causal=is_causal,
            scale=scale,
        )
        return nested_view_from_values_offsets_lengths(
            output,
            query.offsets(),
            query.lengths(),
            min_seqlen=query._maybe_min_seqlen,  # type: ignore[attr-defined]
            max_seqlen=query._maybe_max_seqlen,  # type: ignore[attr-defined]
        )

    compute_logsumexp = query.requires_grad or key.requires_grad or value.requires_grad

    backend_choice = _select_sdp_backend(
        query, key, value, attn_mask, dropout_p, is_causal, enable_gqa
    )

    if _is_computing_meta_flops(query):
        # Backend choice will probably not be correct if we have a meta device,
        # because backend choice is device-aware. In this case, we mostly just
        # want to avoid using math backend (which does a .item() call).
        # Arbitrarily choose flash attention.
        backend_choice = SDPBackend.FLASH_ATTENTION

    if backend_choice == SDPBackend.FLASH_ATTENTION:
        og_size = query.size(-1)
        query_padded = _pad_last_dim(query, 8, False)
        key_padded = _pad_last_dim(key, 8, False)
        value_padded = _pad_last_dim(value, 8, False)
        # We need to calculate the scale based off the OG head dim size
        og_scale = _calculate_scale(query, scale)
        (
            query_buffer_reshaped,
            key_buffer_reshaped,
            value_buffer_reshaped,
            cumulative_sequence_length_q,
            cumulative_sequence_length_kv,
            max_seqlen_batch_q,
            max_seqlen_batch_kv,
            output_nt_info,
        ) = _sdpa_nested_preprocessing(query_padded, key_padded, value_padded)
        (
            attention,
            _logsumexp,
            _philox_seed,
            _philox_offset,
            _debug_attn_mask,
        ) = torch.ops.aten._flash_attention_forward(
            query_buffer_reshaped,
            key_buffer_reshaped,
            value_buffer_reshaped,
            cumulative_sequence_length_q,
            cumulative_sequence_length_kv,
            max_seqlen_batch_q,
            max_seqlen_batch_kv,
            dropout_p,
            is_causal,
            False,
            scale=og_scale,
        )
        # Reshape output to convert nnz to batch_size and seq_len
        attention = nested_view_from_values_offsets_lengths(
            attention,  # output from flash_attn is [total_q, num_heads, head_size_og]
            **output_nt_info,
        ).transpose(1, 2)
        return _post_process_flash_output(attention, og_size)
    elif backend_choice == SDPBackend.EFFICIENT_ATTENTION:
        (
            query_reshaped,
            key_reshaped,
            value_reshaped,
            cumulative_sequence_length_q,
            cumulative_sequence_length_kv,
            max_seqlen_batch_q,
            max_seqlen_batch_kv,
            output_nt_info,
        ) = _sdpa_nested_preprocessing(query, key, value)
        (
            attention,
            log_sumexp,
            seed,
            offset,
            max_seqlen_q,
            max_seqlen_batch_kv,
        ) = torch.ops.aten._efficient_attention_forward(
            query_reshaped.unsqueeze(0),
            key_reshaped.unsqueeze(0),
            value_reshaped.unsqueeze(0),
            None,
            cumulative_sequence_length_q,
            cumulative_sequence_length_kv,
            max_seqlen_batch_q,
            max_seqlen_batch_kv,
            dropout_p,
            int(is_causal),
            compute_logsumexp,
            scale=scale,
        )
        # Reshape output to convert nnz to batch_size and seq_len
        return nested_view_from_values_offsets_lengths(
            attention.squeeze(0),
            **output_nt_info,
        ).transpose(1, 2)
    elif backend_choice == SDPBackend.CUDNN_ATTENTION:
        (
            query_reshaped,
            key_reshaped,
            value_reshaped,
            cumulative_sequence_length_q,
            cumulative_sequence_length_kv,
            max_seqlen_batch_q,
            max_seqlen_batch_kv,
            output_nt_info,
        ) = _sdpa_nested_preprocessing(query, key, value)
        (
            attention,
            logsumexp,
            cum_seqlen_q,
            cum_seqlen_kv,
            max_seqlen_q,
            max_seqlen_kv,
            seed,
            offset,
            _,
        ) = torch.ops.aten._cudnn_attention_forward(
            query_reshaped,
            key_reshaped,
            value_reshaped,
            attn_mask,
            cumulative_sequence_length_q,
            cumulative_sequence_length_kv,
            max_seqlen_batch_q,
            max_seqlen_batch_kv,
            compute_logsumexp,
            dropout_p,
            is_causal,
            False,
            scale=scale,
        )
        return nested_view_from_values_offsets_lengths(
            attention,
            **output_nt_info,
        ).transpose(1, 2)
    elif backend_choice == SDPBackend.MATH:
        # save the offsets and shape of the inputs, so we can reshape the final output
        # query @ key = attn: [B, D1, j0, D'] @ [B, D1, D' j1] = [B, D1, j0, j1]
        # attn @ value = out: [B, D1, j0, j1] @ [B, D1, j1, D2] = [B, D1, j0, D2]
        offsets = query.offsets()
        q_lengths = query.lengths()
        min_seqlen = query._maybe_min_seqlen
        max_seqlen = query._maybe_max_seqlen
        d1 = query._size[1]
        d2 = value._size[-1]

        # convert jagged layout Nested Tensor to strided layout Nested Tensor
        # which support the math implementation of SDPA
        def get_strided_layout_nested_tensor(jagged_layout_nt):
            lengths = jagged_layout_nt._offsets[1:] - jagged_layout_nt._offsets[:-1]
            transpose = torch.transpose(jagged_layout_nt, 1, 2)
            tensor_list = transpose.values().split(list(lengths), dim=0)
            strided_nt = torch.nested.as_nested_tensor(list(tensor_list))
            strided_nt = strided_nt.transpose(1, 2).contiguous()
            return strided_nt

        query = get_strided_layout_nested_tensor(query)
        key = get_strided_layout_nested_tensor(key)
        value = get_strided_layout_nested_tensor(value)

        attn_out = torch._scaled_dot_product_attention_math(
            query, key, value, attn_mask, dropout_p, is_causal, scale=scale
        )[0]

        # convert strided layout Nested Tensor back to jagged layout Nested Tensor
        attn_out = attn_out.transpose(1, 2).contiguous().values()
        attn_out = attn_out.view(-1, d1, d2)
        attn_out = nested_view_from_values_offsets_lengths(
            attn_out,
            offsets,
            lengths=q_lengths,
            min_seqlen=min_seqlen,
            max_seqlen=max_seqlen,
        ).transpose(1, 2)

        return attn_out
    else:
        raise RuntimeError(
            "No viable backend for scaled_dot_product_attention was found."
        )