def _int8_quantize(
    A: torch.Tensor,
    A_scale: torch.Tensor | None,
    per_act_token: bool,
    block_shape: list[int] | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Perform int8 quantization on the inputs.  If a block_shape
    is provided, the output will be blocked.
    """

    # If weights are per-channel (per_channel_quant=True), then
    # activations apply per-token quantization. Otherwise, assume
    # activation tensor-wise fp8/int8 quantization, dynamic or static
    if block_shape is None:
        if per_act_token:
            A, A_scale = per_token_quant_int8(A)
        elif A_scale is not None:
            # Static per-tensor: use the optimized CUDA kernel
            A, A_scale, _ = ops.scaled_int8_quant(A, scale=A_scale)
        elif A_scale is None:
            # Dynamic per-tensor: compute scale then quantize via kernel
            A_scale = torch.clamp(A.abs().max() / 127.0, min=1e-10)
            A, A_scale, _ = ops.scaled_int8_quant(A, scale=A_scale)
    else:
        assert not per_act_token
        assert len(block_shape) == 2
        _, block_k = block_shape[0], block_shape[1]
        A, A_scale = per_token_group_quant_int8(A, block_k)
        assert cdiv(A.size(-1), block_k) == A_scale.size(-1)

    return A, A_scale