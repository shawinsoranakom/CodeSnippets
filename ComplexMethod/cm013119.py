def aten_scaled_dot_product_attention_23(
    query: TFloat,
    key: TFloat,
    value: TFloat,
    attn_mask: TFloat | None = None,
    dropout_p: float = 0.0,
    is_causal: bool = False,
    scale: float | None = None,
    enable_gqa: bool = False,
) -> TFloat:
    """scaled_dot_product_attention(Tensor query, Tensor key, Tensor value, Tensor? attn_mask=None, float dropout_p=0.0, bool is_causal=False, *, float? scale=None, bool enable_gqa=False) -> Tensor

    Reference:
        1. https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html
        2. https://onnx.ai/onnx/operators/onnx__Attention.html

    Attempts to convert SDPA to Attention onnx op and fallbacks to an onnx graph equivalent to the following PyTorch code::
        scale_factor = 1 / math.sqrt(Q.size(-1)) if scale is None else scale
        attn_mask = (
            torch.ones(L, S, dtype=torch.bool).tril(diagonal=0)
            if is_causal
            else attn_mask
        )
        attn_mask = (
            attn_mask.masked_fill(not attn_mask, -float("inf"))
            if attn_mask.dtype == torch.bool
            else attn_mask
        )
        attn_weight = torch.softmax(
            (Q @ K.transpose(-2, -1) * scale_factor) + attn_mask, dim=-1
        )
        attn_weight = torch.dropout(attn_weight, dropout_p)
        return attn_weight @ V

    where Q, K, V are the query, key, and value tensors, respectively.
    L is the target sequence length, S is the source sequence length, and E is the embedding size.
    """
    if is_causal and attn_mask is not None:
        raise AssertionError("is_causal and attn_mask cannot be set at the same time")
    if not (len(query.shape) == 4 and len(key.shape) == 4 and len(value.shape) == 4):
        raise AssertionError("only 4D query, key, and value are supported")

    # Attention onnx op can only handle non-training scenarios where dropout is disabled.
    if dropout_p == 0:
        if enable_gqa:
            if not (
                query.shape[1] > key.shape[1] == value.shape[1]
                and query.shape[1] % key.shape[1] == 0
            ):
                raise AssertionError(
                    "SDPA (GQA or MQA) requires q_num_heads > kv_num_heads & "
                    "q_num_heads % kv_num_heads == 0"
                )
        else:
            if not (query.shape[1] == key.shape[1] == value.shape[1]):
                raise AssertionError("SDPA (MHA) requires q_num_heads = kv_num_heads")

        # NOTE: num_heads attributes (q_num_heads/kv_num_heads) should not be specified for 4D.
        # They are not populated with 4D inputs because this information directly comes from input shapes:
        # `q_num_heads=query.shape[1]` and `kv_num_heads=key.shape[1]`.
        # This dimension is usually static but it could not be dynamic if also given as an attribute.
        # num_heads attributes are needed for 3D attention inputs:
        # (shape: [B, S, N*H]), 4D shape is ([B, N, S, H]).

        Y, _, _, _ = op23.Attention(
            query,
            key,
            value,
            attn_mask=attn_mask,
            scale=scale,
            is_causal=is_causal,
        )
        return Y

    if scale is None:
        scale = _attention_scale(query, op23)
    scale = op23.CastLike(scale, query)

    if is_causal:
        attn_mask = _causal_attention_mask(query, key, op23)

    if enable_gqa:
        key, value = _attention_repeat_kv_for_group_query(query, key, value, op23)

    if attn_mask is None:
        return _aten_scaled_dot_product_attention_no_mask_onnx(
            query, key, value, scale, dropout_p, op23
        )

    return _aten_scaled_dot_product_attention_float_mask_onnx(
        query, key, value, attn_mask, scale, dropout_p, op23
    )