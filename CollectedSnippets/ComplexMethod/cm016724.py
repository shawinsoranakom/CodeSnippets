def attention3_sage(q, k, v, heads, mask=None, attn_precision=None, skip_reshape=False, skip_output_reshape=False, **kwargs):
    exception_fallback = False
    if (q.device.type != "cuda" or
        q.dtype not in (torch.float16, torch.bfloat16) or
        mask is not None):
        return attention_pytorch(
            q, k, v, heads,
            mask=mask,
            attn_precision=attn_precision,
            skip_reshape=skip_reshape,
            skip_output_reshape=skip_output_reshape,
            **kwargs
        )

    if skip_reshape:
        B, H, L, D = q.shape
        if H != heads:
            return attention_pytorch(
                q, k, v, heads,
                mask=mask,
                attn_precision=attn_precision,
                skip_reshape=True,
                skip_output_reshape=skip_output_reshape,
                **kwargs
            )
        q_s, k_s, v_s = q, k, v
        N = q.shape[2]
        dim_head = D
    else:
        B, N, inner_dim = q.shape
        if inner_dim % heads != 0:
            return attention_pytorch(
                q, k, v, heads,
                mask=mask,
                attn_precision=attn_precision,
                skip_reshape=False,
                skip_output_reshape=skip_output_reshape,
                **kwargs
            )
        dim_head = inner_dim // heads

    if dim_head >= 256 or N <= 1024:
        return attention_pytorch(
                q, k, v, heads,
                mask=mask,
                attn_precision=attn_precision,
                skip_reshape=skip_reshape,
                skip_output_reshape=skip_output_reshape,
                **kwargs
            )

    if not skip_reshape:
        q_s, k_s, v_s = map(
            lambda t: t.view(B, -1, heads, dim_head).permute(0, 2, 1, 3).contiguous(),
            (q, k, v),
        )
        B, H, L, D = q_s.shape

    try:
        out = sageattn3_blackwell(q_s, k_s, v_s, is_causal=False)
    except Exception as e:
        exception_fallback = True
        logging.error("Error running SageAttention3: %s, falling back to pytorch attention.", e)

    if exception_fallback:
        if not skip_reshape:
            del q_s, k_s, v_s
        return attention_pytorch(
                q, k, v, heads,
                mask=mask,
                attn_precision=attn_precision,
                skip_reshape=False,
                skip_output_reshape=skip_output_reshape,
                **kwargs
            )

    if skip_reshape:
        if not skip_output_reshape:
            out = out.permute(0, 2, 1, 3).reshape(B, L, H * D)
    else:
        if skip_output_reshape:
            pass
        else:
            out = out.permute(0, 2, 1, 3).reshape(B, L, H * D)

    return out