def sdpa_dense_backward(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    out: torch.Tensor,
    logsumexp: torch.Tensor,
    grad_out: torch.Tensor | None,
    grad_logsumexp: torch.Tensor | None,
    fw_graph: Callable,  # GraphModule type hint?
    joint_graph: Callable,
    block_mask: tuple,
    scale: float,
    kernel_options: dict[str, Any],
    score_mod_other_buffers: tuple,
    mask_mod_other_buffers: tuple,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, tuple[torch.Tensor | None, ...]]:
    if query.dtype != key.dtype or query.dtype != value.dtype:
        raise ValueError(
            f"Backward pass with mixed query, key, and value dtype is not supported, "
            f"got query.dtype={query.dtype}, key.dtype={key.dtype}, "
            f"and value.dtype={value.dtype}"
        )
    if joint_graph is None:
        example_vals = (
            query.new_zeros((), requires_grad=True),
            query.new_zeros((), dtype=torch.int),
            query.new_zeros((), dtype=torch.int),
            query.new_zeros((), dtype=torch.int),
            query.new_zeros((), dtype=torch.int),
        )
        _, joint_graph = create_fw_bw_graph(
            fw_graph, example_vals, score_mod_other_buffers
        )
    from torch._dynamo._trace_wrapped_higher_order_op import TransformGetItemToIndex

    Bq, Hq, seq_len_q, qk_head_dim = query.shape
    Bkv, Hkv, seq_len_kv, v_head_dim = value.shape

    # Get outputs before calling repeat interleave and permute to input stride orders
    actual_grad_query = query.new_empty((Bq, Hq, seq_len_q, qk_head_dim))
    actual_grad_query = _permute_strides(actual_grad_query, query.stride())

    actual_grad_key = key.new_empty((Bq, Hkv, seq_len_kv, qk_head_dim))
    actual_grad_key = _permute_strides(actual_grad_key, key.stride())

    actual_grad_value = value.new_empty((Bq, Hkv, seq_len_kv, v_head_dim))
    actual_grad_value = _permute_strides(actual_grad_value, value.stride())

    def _maybe_new_buffer(
        buffer: torch.Tensor | torch.SymInt | int,
    ) -> torch.Tensor | torch.SymInt | int | None:
        if isinstance(buffer, torch.Tensor):
            return (
                torch.empty_like(buffer, memory_format=torch.contiguous_format)
                if buffer.requires_grad
                else None
            )
        return buffer

    actual_grad_score_mod_captured = [
        _maybe_new_buffer(buffer) for buffer in score_mod_other_buffers
    ]

    Bq, Bkv = query.size(0), key.size(0)
    if not ((Bq == Bkv) or (Bq > 1 and Bkv == 1)):
        raise RuntimeError(f"Bq and Bkv must broadcast. Got Bq={Bq} and Bkv={Bkv}")

    key = key.expand((Bq, *key.size()[1:]))
    value = value.expand((Bq, *value.size()[1:]))

    G = query.size(1) // key.size(1)
    key = torch.repeat_interleave(key, G, dim=1)
    value = torch.repeat_interleave(value, G, dim=1)

    if grad_out is None:
        grad_out = torch.zeros_like(out)
    if grad_logsumexp is None:
        grad_logsumexp = torch.zeros_like(logsumexp)

    # logsumexp is expected in log2 scale (as returned by the forward HOP).
    # The public flex_attention API converts lse to natural log before returning,
    # so callers using the public API must not pass that value here directly.
    logsumexp = logsumexp * math.log(2)
    # The backwards formula for the log -> log2 change of base in the forwards
    grad_logsumexp = grad_logsumexp / math.log(2)
    scores, post_mod_scores = _math_attention_inner(
        query,
        key,
        value,
        fw_graph,
        block_mask,
        scale,
        kernel_options,
        score_mod_other_buffers,
        mask_mod_other_buffers,
    )
    masked_out_rows = logsumexp == -float("inf")
    softmax_scores = torch.exp(post_mod_scores - logsumexp.unsqueeze(-1))
    softmax_scores = torch.where(masked_out_rows.unsqueeze(-1), 0, softmax_scores)

    grad_value = softmax_scores.to(query.dtype).transpose(-2, -1) @ grad_out

    grad_softmax_scores = grad_out.to(dtype=softmax_scores.dtype) @ value.to(
        dtype=softmax_scores.dtype
    ).transpose(-2, -1)

    sum_scores = torch.sum(
        out.to(dtype=softmax_scores.dtype) * grad_out.to(dtype=softmax_scores.dtype),
        -1,
        keepdim=True,
    )
    grad_score_mod = softmax_scores * (
        grad_softmax_scores - sum_scores + grad_logsumexp.unsqueeze(-1)
    )

    b = torch.arange(0, scores.size(0), device=scores.device)
    h = torch.arange(0, scores.size(1), device=scores.device)
    m = torch.arange(0, scores.size(2), device=scores.device)
    n = torch.arange(0, scores.size(3), device=scores.device)

    mask_graph = block_mask[-1]
    # Gradient of the inline score_mod function, with respect to the scores
    captured_buffers_in_dim = (None,) * len(score_mod_other_buffers)
    out_dims = [0, None, None, None, None] + [None] * len(score_mod_other_buffers)
    from torch.nn.attention.flex_attention import _vmap_for_bhqkv

    # inputs are [score, b, h, q_idx, kv_idx, gradOut, ...]
    # score and gradOut are "fully" batched
    joint_score_mod = _vmap_for_bhqkv(
        joint_graph,
        prefix=(0,),
        suffix=(0,) + captured_buffers_in_dim,
        out_dims=out_dims,
    )
    with TransformGetItemToIndex():
        grad_scores, _, _, _, _, *grad_score_mod_captured = joint_score_mod(
            scores, b, h, m, n, grad_score_mod, *score_mod_other_buffers
        )
    grad_scores = grad_scores * scale
    grad_scores = grad_scores.to(query.dtype)

    mask_mod = _vmap_for_bhqkv(
        mask_graph, prefix=(), suffix=(None,) * len(mask_mod_other_buffers)
    )
    with TransformGetItemToIndex():
        mask_scores = mask_mod(b, h, m, n, *mask_mod_other_buffers)
        grad_scores = torch.where(
            mask_scores, grad_scores, torch.tensor(0, dtype=query.dtype)
        )

    grad_query = grad_scores @ key
    grad_key = grad_scores.transpose(-2, -1) @ query

    # Reduce DK, DV along broadcasted heads.
    grad_key = grad_key.view(
        grad_key.size(0), -1, G, grad_key.size(-2), grad_key.size(-1)
    )
    grad_value = grad_value.view(
        grad_value.size(0), -1, G, grad_value.size(-2), grad_value.size(-1)
    )

    grad_key = torch.sum(grad_key, 2, keepdim=False)
    grad_value = torch.sum(grad_value, 2, keepdim=False)

    # Fill to correctly strided outputs
    actual_grad_query.copy_(grad_query)
    actual_grad_key.copy_(grad_key)
    actual_grad_value.copy_(grad_value)

    if Bq != Bkv:
        if not (Bq > 1 and Bkv == 1):
            raise AssertionError(
                f"Bq and Bkv must broadcast. Got Bq={Bq} and Bkv={Bkv}"
            )

        actual_grad_key = torch.sum(actual_grad_key, 0, keepdim=True)
        actual_grad_value = torch.sum(actual_grad_value, 0, keepdim=True)

    score_mod_other_buffer_grads = [
        actual_grad.copy_(grad) if isinstance(actual_grad, torch.Tensor) else None
        for actual_grad, grad in zip(
            actual_grad_score_mod_captured, grad_score_mod_captured
        )
    ]

    return (
        actual_grad_query,
        actual_grad_key,
        actual_grad_value,
        tuple(score_mod_other_buffer_grads),
    )