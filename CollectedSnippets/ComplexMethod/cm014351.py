def sdpa_backward_flop_count(grad_out_shape, query_shape, key_shape, value_shape):
    b, h_q, s_q, d_q = query_shape
    _b2, h_kv, s_k, _d2 = key_shape
    _b3, _h3, _s3, d_v = value_shape
    _b4, _h4, _s4, _d4 = grad_out_shape
    if not (b == _b2 == _b3 == _b4 and h_kv == _h3 and h_q == _h4):
        raise AssertionError(
            "sdpa_backward_flop_count: batch/heads mismatch among tensors"
        )
    if h_q < h_kv or h_q % h_kv != 0:
        raise AssertionError(
            f"sdpa_backward_flop_count: query heads ({h_q}) must be a multiple of "
            f"key/value heads ({h_kv})"
        )
    if not (d_q == _d2 and d_v == _d4 and s_k == _s3 and s_q == _s4):
        raise AssertionError(
            "sdpa_backward_flop_count: grad_out/value/key/query shapes are incompatible"
        )
    total_flops = 0
    # Step 1: We recompute the scores matrix.
    # q: [b, h_q, s_q, d_q] @ k: [b, h_q, d_q, s_k] -> scores: [b, h_q, s_q, s_k]
    total_flops += bmm_flop((b * h_q, s_q, d_q), (b * h_q, d_q, s_k))

    # Step 2: We propagate the gradients through the score @ v operation.
    # gradOut: [b, h_q, s_q, d_v] @ v: [b, h_q, d_v, s_k] -> gradScores: [b, h_q, s_q, s_k]
    total_flops += bmm_flop((b * h_q, s_q, d_v), (b * h_q, d_v, s_k))
    # scores: [b, h_q, s_k, s_q] @ gradOut: [b, h_q, s_q, d_v] -> gradV: [b, h_q, s_k, d_v]
    total_flops += bmm_flop((b * h_q, s_k, s_q), (b * h_q, s_q, d_v))

    # Step 3: We propagate th gradients through the k @ v operation
    # gradScores: [b, h_q, s_q, s_k] @ k: [b, h_q, s_k, d_q] -> gradQ: [b, h_q, s_q, d_q]
    total_flops += bmm_flop((b * h_q, s_q, s_k), (b * h_q, s_k, d_q))
    # q: [b, h_q, d_q, s_q] @ gradScores: [b, h_q, s_q, s_k] -> gradK: [b, h_q, d_q, s_k]
    total_flops += bmm_flop((b * h_q, d_q, s_q), (b * h_q, s_q, s_k))
    return total_flops