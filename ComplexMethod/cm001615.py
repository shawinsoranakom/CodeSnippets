def torch_xpu_scaled_dot_product_attention(
    query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False, *args, **kwargs
):
    # cast to same dtype first
    key = key.to(query.dtype)
    value = value.to(query.dtype)
    if attn_mask is not None and attn_mask.dtype != torch.bool:
        attn_mask = attn_mask.to(query.dtype)

    N = query.shape[:-2]  # Batch size
    L = query.size(-2)  # Target sequence length
    E = query.size(-1)  # Embedding dimension of the query and key
    S = key.size(-2)  # Source sequence length
    Ev = value.size(-1)  # Embedding dimension of the value

    total_batch_size = torch.numel(torch.empty(N))
    device_id = query.device.index
    if device_id not in ARC_SINGLE_ALLOCATION_LIMIT:
        ARC_SINGLE_ALLOCATION_LIMIT[device_id] = min(torch.xpu.get_device_properties(device_id).total_memory // 8, 4 * 1024 * 1024 * 1024)
    batch_size_limit = max(1, ARC_SINGLE_ALLOCATION_LIMIT[device_id] // (L * S * query.element_size()))

    if total_batch_size <= batch_size_limit:
        return orig_sdp_attn_func(
            query,
            key,
            value,
            attn_mask,
            dropout_p,
            is_causal,
            *args, **kwargs
        )

    query = torch.reshape(query, (-1, L, E))
    key = torch.reshape(key, (-1, S, E))
    value = torch.reshape(value, (-1, S, Ev))
    if attn_mask is not None:
        attn_mask = attn_mask.view(-1, L, S)
    chunk_count = (total_batch_size + batch_size_limit - 1) // batch_size_limit
    outputs = []
    for i in range(chunk_count):
        attn_mask_chunk = (
            None
            if attn_mask is None
            else attn_mask[i * batch_size_limit : (i + 1) * batch_size_limit, :, :]
        )
        chunk_output = orig_sdp_attn_func(
            query[i * batch_size_limit : (i + 1) * batch_size_limit, :, :],
            key[i * batch_size_limit : (i + 1) * batch_size_limit, :, :],
            value[i * batch_size_limit : (i + 1) * batch_size_limit, :, :],
            attn_mask_chunk,
            dropout_p,
            is_causal,
            *args, **kwargs
        )
        outputs.append(chunk_output)
    result = torch.cat(outputs, dim=0)
    return torch.reshape(result, (*N, L, Ev))