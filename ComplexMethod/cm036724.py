def moe_quantize_weights(
    w: torch.Tensor,
    w_s: torch.Tensor | None,
    quant_dtype: torch.dtype | str | None,
    per_token_quant: bool,
    block_shape: list[int] | None,
) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
    assert w.dim() == 3
    e, rows, cols = w.shape
    w_l = [None] * e
    w_s_l = [None] * e
    w_gs_l = [None] * e
    for idx in range(e):
        w_l[idx], w_s_l[idx], w_gs_l[idx] = moe_quantize_weights_2d(
            w[idx], None, quant_dtype, per_token_quant, block_shape
        )

    w = torch.stack(w_l)
    w_s = torch.stack(w_s_l)
    w_gs = torch.stack(w_gs_l) if e > 0 and w_gs_l[0] is not None else None

    if w_s.ndim == 2:
        assert w_s.shape[-1] == 1
        w_s = w_s.view(-1, 1, 1)

    if block_shape is not None:
        block_n, block_k = block_shape
        n_tiles = (rows + block_n - 1) // block_n
        k_tiles = (cols + block_k - 1) // block_k
        assert w_s.shape == (e, n_tiles, k_tiles)

    return w, w_s, w_gs