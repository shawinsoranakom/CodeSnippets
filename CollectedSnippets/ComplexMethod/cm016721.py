def attention_xformers(q, k, v, heads, mask=None, attn_precision=None, skip_reshape=False, skip_output_reshape=False, **kwargs):
    b = q.shape[0]
    dim_head = q.shape[-1]
    # check to make sure xformers isn't broken
    disabled_xformers = False

    if BROKEN_XFORMERS:
        if b * heads > 65535:
            disabled_xformers = True

    if not disabled_xformers:
        if torch.jit.is_tracing() or torch.jit.is_scripting():
            disabled_xformers = True

    if disabled_xformers:
        return attention_pytorch(q, k, v, heads, mask, skip_reshape=skip_reshape, **kwargs)

    if skip_reshape:
        # b h k d -> b k h d
        q, k, v = map(
            lambda t: t.permute(0, 2, 1, 3),
            (q, k, v),
        )
    # actually do the reshaping
    else:
        dim_head //= heads
        q, k, v = map(
            lambda t: t.reshape(b, -1, heads, dim_head),
            (q, k, v),
        )

    if mask is not None:
        # add a singleton batch dimension
        if mask.ndim == 2:
            mask = mask.unsqueeze(0)
        # add a singleton heads dimension
        if mask.ndim == 3:
            mask = mask.unsqueeze(1)
        # pad to a multiple of 8
        pad = 8 - mask.shape[-1] % 8
        # the xformers docs says that it's allowed to have a mask of shape (1, Nq, Nk)
        # but when using separated heads, the shape has to be (B, H, Nq, Nk)
        # in flux, this matrix ends up being over 1GB
        # here, we create a mask with the same batch/head size as the input mask (potentially singleton or full)
        mask_out = torch.empty([mask.shape[0], mask.shape[1], q.shape[1], mask.shape[-1] + pad], dtype=q.dtype, device=q.device)

        mask_out[..., :mask.shape[-1]] = mask
        # doesn't this remove the padding again??
        mask = mask_out[..., :mask.shape[-1]]
        mask = mask.expand(b, heads, -1, -1)

    out = xformers.ops.memory_efficient_attention(q, k, v, attn_bias=mask)

    if skip_output_reshape:
        out = out.permute(0, 2, 1, 3)
    else:
        out = (
            out.reshape(b, -1, heads * dim_head)
        )

    return out