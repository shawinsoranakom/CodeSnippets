def attention_sub_quad(query, key, value, heads, mask=None, attn_precision=None, skip_reshape=False, skip_output_reshape=False, **kwargs):
    attn_precision = get_attn_precision(attn_precision, query.dtype)

    if skip_reshape:
        b, _, _, dim_head = query.shape
    else:
        b, _, dim_head = query.shape
        dim_head //= heads

    if skip_reshape:
        query = query.reshape(b * heads, -1, dim_head)
        value = value.reshape(b * heads, -1, dim_head)
        key = key.reshape(b * heads, -1, dim_head).movedim(1, 2)
    else:
        query = query.unsqueeze(3).reshape(b, -1, heads, dim_head).permute(0, 2, 1, 3).reshape(b * heads, -1, dim_head)
        value = value.unsqueeze(3).reshape(b, -1, heads, dim_head).permute(0, 2, 1, 3).reshape(b * heads, -1, dim_head)
        key = key.unsqueeze(3).reshape(b, -1, heads, dim_head).permute(0, 2, 3, 1).reshape(b * heads, dim_head, -1)


    dtype = query.dtype
    upcast_attention = attn_precision == torch.float32 and query.dtype != torch.float32
    if upcast_attention:
        bytes_per_token = torch.finfo(torch.float32).bits//8
    else:
        bytes_per_token = torch.finfo(query.dtype).bits//8
    batch_x_heads, q_tokens, _ = query.shape
    _, _, k_tokens = key.shape

    mem_free_total, _ = model_management.get_free_memory(query.device, True)

    kv_chunk_size_min = None
    kv_chunk_size = None
    query_chunk_size = None

    for x in [4096, 2048, 1024, 512, 256]:
        count = mem_free_total / (batch_x_heads * bytes_per_token * x * 4.0)
        if count >= k_tokens:
            kv_chunk_size = k_tokens
            query_chunk_size = x
            break

    if query_chunk_size is None:
        query_chunk_size = 512

    if mask is not None:
        if len(mask.shape) == 2:
            bs = 1
        else:
            bs = mask.shape[0]
        mask = mask.reshape(bs, -1, mask.shape[-2], mask.shape[-1]).expand(b, heads, -1, -1).reshape(-1, mask.shape[-2], mask.shape[-1])

    hidden_states = efficient_dot_product_attention(
        query,
        key,
        value,
        query_chunk_size=query_chunk_size,
        kv_chunk_size=kv_chunk_size,
        kv_chunk_size_min=kv_chunk_size_min,
        use_checkpoint=False,
        upcast_attention=upcast_attention,
        mask=mask,
    )

    hidden_states = hidden_states.to(dtype)
    if skip_output_reshape:
        hidden_states = hidden_states.unflatten(0, (-1, heads))
    else:
        hidden_states = hidden_states.unflatten(0, (-1, heads)).transpose(1,2).flatten(start_dim=2)
    return hidden_states