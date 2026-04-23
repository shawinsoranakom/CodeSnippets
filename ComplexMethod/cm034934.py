def multi_head_attention_forward(
    query: paddle.Tensor,
    key: paddle.Tensor,
    value: paddle.Tensor,
    embed_dim_to_check: int,
    num_heads: int,
    in_proj_weight: paddle.Tensor,
    in_proj_bias: Optional[paddle.Tensor],
    bias_k: Optional[paddle.Tensor],
    bias_v: Optional[paddle.Tensor],
    add_zero_attn: bool,
    dropout_p: float,
    out_proj_weight: paddle.Tensor,
    out_proj_bias: Optional[paddle.Tensor],
    training: bool = True,
    key_padding_mask: Optional[paddle.Tensor] = None,
    need_weights: bool = True,
    attn_mask: Optional[paddle.Tensor] = None,
    use_separate_proj_weight: bool = False,
    q_proj_weight: Optional[paddle.Tensor] = None,
    k_proj_weight: Optional[paddle.Tensor] = None,
    v_proj_weight: Optional[paddle.Tensor] = None,
    static_k: Optional[paddle.Tensor] = None,
    static_v: Optional[paddle.Tensor] = None,
    is_export=False,
):

    tgt_len, bsz, embed_dim = query.shape
    src_len, _, _ = key.shape

    if isinstance(embed_dim, paddle.Tensor):
        head_dim = embed_dim.div(num_heads, rounding_mode="trunc")
    else:
        head_dim = embed_dim // num_heads
    q, k, v = _in_projection_packed(
        query, key, value, in_proj_weight, in_proj_bias, is_export
    )

    if key_padding_mask is not None and key_padding_mask.dtype == paddle.uint8:
        warnings.warn(
            "Byte tensor for key_padding_mask in nn.MultiheadAttention is deprecated. Use bool tensor instead."
        )
        key_padding_mask = key_padding_mask.to(paddle.bool)

    if bias_k is not None and bias_v is not None:  # False
        assert static_k is None, "bias cannot be added to static key."
        assert static_v is None, "bias cannot be added to static value."
        k = paddle.concat([k, bias_k.repeat(1, bsz, 1)])
        v = paddle.concat([v, bias_v.repeat(1, bsz, 1)])
    else:
        assert bias_k is None
        assert bias_v is None

    q = q.reshape([tgt_len, bsz * num_heads, head_dim]).transpose([1, 0, 2])
    if static_k is None:  # True
        k = k.reshape([k.shape[0], bsz * num_heads, head_dim]).transpose([1, 0, 2])
    else:
        assert (
            static_k.shape[0] == bsz * num_heads
        ), f"expecting static_k.size(0) of {bsz * num_heads}, but got {static_k.shape[0]}"
        assert (
            static_k.shape[2] == head_dim
        ), f"expecting static_k.size(2) of {head_dim}, but got {static_k.shape[2]}"
        k = static_k
    if static_v is None:  # True
        v = v.reshape([v.shape[0], bsz * num_heads, head_dim]).transpose([1, 0, 2])
    else:
        assert (
            static_v.shape[0] == bsz * num_heads
        ), f"expecting static_v.size(0) of {bsz * num_heads}, but got {static_v.shape[0]}"
        assert (
            static_v.shape[2] == head_dim
        ), f"expecting static_v.size(2) of {head_dim}, but got {static_v.shape[2]}"
        v = static_v

    src_len = k.shape[1]

    if not training:
        dropout_p = 0.0

    attn_output, attn_output_weights = _scaled_dot_product_attention(
        q, k, v, attn_mask, dropout_p
    )

    attn_output = attn_output.transpose([1, 0, 2]).reshape([tgt_len, bsz, embed_dim])
    attn_output = linear(
        attn_output, out_proj_weight, out_proj_bias, is_transpose=False
    )

    if need_weights:
        attn_output_weights = attn_output_weights.reshape(
            [bsz, num_heads, tgt_len, src_len]
        )
        return attn_output, attn_output_weights.sum(axis=1) / num_heads
    else:
        return attn_output, None