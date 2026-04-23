def efficient_dot_product_attention(
    query: Tensor,
    key_t: Tensor,
    value: Tensor,
    query_chunk_size=1024,
    kv_chunk_size: Optional[int] = None,
    kv_chunk_size_min: Optional[int] = None,
    use_checkpoint=True,
    upcast_attention=False,
    mask = None,
):
    """Computes efficient dot-product attention given query, transposed key, and value.
      This is efficient version of attention presented in
      https://arxiv.org/abs/2112.05682v2 which comes with O(sqrt(n)) memory requirements.
      Args:
        query: queries for calculating attention with shape of
          `[batch * num_heads, tokens, channels_per_head]`.
        key_t: keys for calculating attention with shape of
          `[batch * num_heads, channels_per_head, tokens]`.
        value: values to be used in attention with shape of
          `[batch * num_heads, tokens, channels_per_head]`.
        query_chunk_size: int: query chunks size
        kv_chunk_size: Optional[int]: key/value chunks size. if None: defaults to sqrt(key_tokens)
        kv_chunk_size_min: Optional[int]: key/value minimum chunk size. only considered when kv_chunk_size is None. changes `sqrt(key_tokens)` into `max(sqrt(key_tokens), kv_chunk_size_min)`, to ensure our chunk sizes don't get too small (smaller chunks = more chunks = less concurrent work done).
        use_checkpoint: bool: whether to use checkpointing (recommended True for training, False for inference)
      Returns:
        Output of shape `[batch * num_heads, query_tokens, channels_per_head]`.
      """
    batch_x_heads, q_tokens, q_channels_per_head = query.shape
    _, _, k_tokens = key_t.shape
    scale = q_channels_per_head ** -0.5

    kv_chunk_size = min(kv_chunk_size or int(math.sqrt(k_tokens)), k_tokens)
    if kv_chunk_size_min is not None:
        kv_chunk_size = max(kv_chunk_size, kv_chunk_size_min)

    if mask is not None and len(mask.shape) == 2:
        mask = mask.unsqueeze(0)

    def get_query_chunk(chunk_idx: int) -> Tensor:
        return dynamic_slice(
            query,
            (0, chunk_idx, 0),
            (batch_x_heads, min(query_chunk_size, q_tokens), q_channels_per_head)
        )

    def get_mask_chunk(chunk_idx: int) -> Tensor:
        if mask is None:
            return None
        if mask.shape[1] == 1:
            return mask
        chunk = min(query_chunk_size, q_tokens)
        return mask[:,chunk_idx:chunk_idx + chunk]

    summarize_chunk: SummarizeChunk = partial(_summarize_chunk, scale=scale, upcast_attention=upcast_attention)
    summarize_chunk: SummarizeChunk = partial(checkpoint, summarize_chunk) if use_checkpoint else summarize_chunk
    compute_query_chunk_attn: ComputeQueryChunkAttn = partial(
        _get_attention_scores_no_kv_chunking,
        scale=scale,
        upcast_attention=upcast_attention
    ) if k_tokens <= kv_chunk_size else (
        # fast-path for when there's just 1 key-value chunk per query chunk (this is just sliced attention btw)
        partial(
            _query_chunk_attention,
            kv_chunk_size=kv_chunk_size,
            summarize_chunk=summarize_chunk,
        )
    )

    if q_tokens <= query_chunk_size:
        # fast-path for when there's just 1 query chunk
        return compute_query_chunk_attn(
            query=query,
            key_t=key_t,
            value=value,
            mask=mask,
        )

    # TODO: maybe we should use torch.empty_like(query) to allocate storage in-advance,
    # and pass slices to be mutated, instead of torch.cat()ing the returned slices
    res = torch.cat([
        compute_query_chunk_attn(
            query=get_query_chunk(i * query_chunk_size),
            key_t=key_t,
            value=value,
            mask=get_mask_chunk(i * query_chunk_size)
        ) for i in range(math.ceil(q_tokens / query_chunk_size))
    ], dim=1)
    return res