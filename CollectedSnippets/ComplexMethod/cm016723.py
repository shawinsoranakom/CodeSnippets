def attention_sage(q, k, v, heads, mask=None, attn_precision=None, skip_reshape=False, skip_output_reshape=False, **kwargs):
    if kwargs.get("low_precision_attention", True) is False:
        return attention_pytorch(q, k, v, heads, mask=mask, skip_reshape=skip_reshape, skip_output_reshape=skip_output_reshape, **kwargs)

    exception_fallback = False
    if skip_reshape:
        b, _, _, dim_head = q.shape
        tensor_layout = "HND"
    else:
        b, _, dim_head = q.shape
        dim_head //= heads
        q, k, v = map(
            lambda t: t.view(b, -1, heads, dim_head),
            (q, k, v),
        )
        tensor_layout = "NHD"

    if mask is not None:
        # add a batch dimension if there isn't already one
        if mask.ndim == 2:
            mask = mask.unsqueeze(0)
        # add a heads dimension if there isn't already one
        if mask.ndim == 3:
            mask = mask.unsqueeze(1)

    try:
        out = sageattn(q, k, v, attn_mask=mask, is_causal=False, tensor_layout=tensor_layout)
    except Exception as e:
        logging.error("Error running sage attention: {}, using pytorch attention instead.".format(e))
        exception_fallback = True
    if exception_fallback:
        if tensor_layout == "NHD":
            q, k, v = map(
                lambda t: t.transpose(1, 2),
                (q, k, v),
            )
        return attention_pytorch(q, k, v, heads, mask=mask, skip_reshape=True, skip_output_reshape=skip_output_reshape, **kwargs)

    if tensor_layout == "HND":
        if not skip_output_reshape:
            out = (
                out.transpose(1, 2).reshape(b, -1, heads * dim_head)
            )
    else:
        if skip_output_reshape:
            out = out.transpose(1, 2)
        else:
            out = out.reshape(b, -1, heads * dim_head)
    return out