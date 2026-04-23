def test_silu_and_mul_per_block_quant(
    default_vllm_config,
    num_tokens: int,
    hidden_size: int,
    has_scale_ub: bool,
    dtype: torch.dtype,
    quant_dtype: torch.dtype,
    group_size: int,
    is_scale_transposed: bool,
    seed: int,
    device_idx: str,
) -> None:
    """Test SiLU+Mul+Block Quantization kernel correctness."""
    torch.accelerator.set_device_index(device_idx)
    device = f"cuda:{device_idx}"
    torch.random.manual_seed(seed)
    torch.set_default_device(device)

    if hidden_size % group_size != 0:
        return

    if has_scale_ub:
        pytest.skip("Scale upper bound not yet supported")

    scale = 1 / hidden_size
    x = torch.randn(num_tokens, hidden_size * 2, dtype=dtype, device=device) * scale

    # Reference implementation
    ref_out, ref_scales = ref_silu_and_mul_per_block_quant(x, quant_dtype, group_size)

    # Fused kernel implementation
    ops_out, ops_scales = ops.silu_and_mul_per_block_quant(
        x, group_size, quant_dtype, None, is_scale_transposed
    )

    # Check for NaN/Inf
    assert not torch.isnan(ops_out.float()).any(), "Kernel output contains NaN"
    assert not torch.isinf(ops_out.float()).any(), "Kernel output contains Inf"
    assert not torch.isnan(ops_scales).any(), "Kernel scales contain NaN"
    assert not torch.isinf(ops_scales).any(), "Kernel scales contain Inf"

    # Check dtypes
    assert ref_out.dtype == quant_dtype
    assert ops_out.dtype == quant_dtype

    # Check scales match
    torch.testing.assert_close(ref_scales, ops_scales, rtol=1e-5, atol=1e-5)

    # Check output correctness via dequantized values
    ref_scales_expanded = ref_scales.repeat_interleave(group_size, dim=1)
    ops_scales_expanded = ops_scales.repeat_interleave(group_size, dim=1)
    ref_deq = ref_out.to(dtype=torch.float32) * ref_scales_expanded
    ops_deq = ops_out.to(dtype=torch.float32) * ops_scales_expanded
    torch.testing.assert_close(ref_deq, ops_deq, atol=5e-2, rtol=5e-2)

    # opcheck
    output = torch.empty(num_tokens, hidden_size, device=device, dtype=quant_dtype)
    num_groups = hidden_size // group_size
    if is_scale_transposed:
        scales = torch.empty(num_groups, num_tokens, device=device, dtype=torch.float32)
    else:
        scales = torch.empty(num_tokens, num_groups, device=device, dtype=torch.float32)
    opcheck(
        torch.ops._C.silu_and_mul_per_block_quant,
        (output, x, scales, group_size, None, is_scale_transposed),
    )