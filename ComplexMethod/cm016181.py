def generate_eager_sdpa(
    attn_type: str,
    shape: tuple[int, ...],
    dtype: torch.dtype,
    block_mask: BlockMask,
    score_mod: Callable | None = None,
    **kwargs,
) -> Callable | None:
    B, Hq, M, Hkv, N, D = shape
    is_decoding = M == 1
    if attn_type == "sliding_window" or attn_type == "prefix_lm":
        attn_mask = create_mask(block_mask.mask_mod, 1, 1, M, N, device="cuda")
    elif attn_type == "rel":
        attn_mask = generate_attn_mask_linear_score_mod(
            [1, 1, M, N], block_mask, score_mod, dtype
        )
    elif attn_type == "head_bias":
        h = torch.arange(Hq, dtype=int, device="cuda")
        attn_mask = (2 * h[None, :, None, None]).broadcast_to(1, Hq, M, N).to(dtype)
    elif attn_type == "alibi":
        attn_mask = generate_attn_mask_linear_score_mod(
            [1, Hq, M, N], block_mask, score_mod, dtype
        )
    else:
        attn_mask = None

    sdpa_dict = {
        "noop": partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        ),
        "causal": partial(
            F.scaled_dot_product_attention, is_causal=True, enable_gqa=(Hq != Hkv)
        ),
        "rel": partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        ),
        "head_bias": partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        ),
        "alibi": partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        ),
        "sliding_window": partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        ),
        "document_mask": partial(
            F.scaled_dot_product_attention, is_causal=True, enable_gqa=(Hq != Hkv)
        )
        if Hq == Hkv
        else None,
        "prefix_lm": partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        ),
        "softcap": None,
    }

    if is_decoding and attn_type == "causal":
        attn_mask = create_mask(block_mask.mask_mod, 1, 1, M, N, device="cuda")
        sdpa_dict["causal"] = partial(
            F.scaled_dot_product_attention, is_causal=False, enable_gqa=(Hq != Hkv)
        )

    return (
        partial(sdpa_dict[attn_type], attn_mask=attn_mask)
        if sdpa_dict[attn_type]
        else None
    )