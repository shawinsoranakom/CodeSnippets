def use_rocm_custom_paged_attention(
    qtype: torch.dtype,
    head_size: int,
    block_size: int,
    gqa_ratio: int,
    max_seq_len: int,
    sliding_window: int,
    kv_cache_dtype: str,
    alibi_slopes: torch.Tensor | None = None,
    sinks: torch.Tensor | None = None,
) -> bool:
    # custom paged attn always supported on V0. On V1, requires sliding window
    # disabled due to observed numerical discrepancy.
    if _ON_GFX9:
        return (
            (sliding_window == 0 or sliding_window == (-1, -1))
            and (qtype == torch.half or qtype == torch.bfloat16)
            and (head_size == 64 or head_size == 128)
            and (block_size == 16 or block_size == 32)
            and (gqa_ratio >= 1 and gqa_ratio <= 16)
            and max_seq_len <= 128 * 1024
            and sinks is None
        )

    else:
        return (
            _ON_GFX1X
            and (sliding_window == 0 or sliding_window == (-1, -1))
            and (qtype == torch.half or qtype == torch.bfloat16)
            and head_size == 128
            and block_size == 16
            and (gqa_ratio >= 3 and gqa_ratio <= 16)
            and max_seq_len <= 128 * 1024
            and alibi_slopes is None
            and kv_cache_dtype == "auto"
            and sinks is None
        )