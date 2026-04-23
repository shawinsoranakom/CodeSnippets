def sub_quad_attention(q, k, v, q_chunk_size=1024, kv_chunk_size=None, kv_chunk_size_min=None, chunk_threshold=None, use_checkpoint=True):
    bytes_per_token = torch.finfo(q.dtype).bits//8
    batch_x_heads, q_tokens, _ = q.shape
    _, k_tokens, _ = k.shape
    qk_matmul_size_bytes = batch_x_heads * bytes_per_token * q_tokens * k_tokens

    if chunk_threshold is None:
        if q.device.type == 'mps':
            chunk_threshold_bytes = 268435456 * (2 if platform.processor() == 'i386' else bytes_per_token)
        else:
            chunk_threshold_bytes = int(get_available_vram() * 0.7)
    elif chunk_threshold == 0:
        chunk_threshold_bytes = None
    else:
        chunk_threshold_bytes = int(0.01 * chunk_threshold * get_available_vram())

    if kv_chunk_size_min is None and chunk_threshold_bytes is not None:
        kv_chunk_size_min = chunk_threshold_bytes // (batch_x_heads * bytes_per_token * (k.shape[2] + v.shape[2]))
    elif kv_chunk_size_min == 0:
        kv_chunk_size_min = None

    if chunk_threshold_bytes is not None and qk_matmul_size_bytes <= chunk_threshold_bytes:
        # the big matmul fits into our memory limit; do everything in 1 chunk,
        # i.e. send it down the unchunked fast-path
        kv_chunk_size = k_tokens

    with devices.without_autocast(disable=q.dtype == v.dtype):
        return sub_quadratic_attention.efficient_dot_product_attention(
            q,
            k,
            v,
            query_chunk_size=q_chunk_size,
            kv_chunk_size=kv_chunk_size,
            kv_chunk_size_min = kv_chunk_size_min,
            use_checkpoint=use_checkpoint,
        )