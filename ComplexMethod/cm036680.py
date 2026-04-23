def test_quantfp8_group_functionality(
    default_vllm_config,
    batch_size: int,
    hidden_dim: int,
    group_size: int,
    seed: int,
    use_ue8m0: bool,
) -> None:
    """Test QuantFP8 group quantization with various configurations.

    Tests both CUDA and native implementations, column-major scales,
    and verifies consistency between implementations.
    """
    set_random_seed(seed)

    x = torch.randn((batch_size, hidden_dim), dtype=torch.bfloat16, device="cuda") * 8
    expected_num_groups = (hidden_dim + group_size - 1) // group_size
    is_divisible = hidden_dim % group_size == 0

    group_shape = GroupShape(1, group_size)
    quant_op = QuantFP8(
        static=False,
        group_shape=group_shape,
        column_major_scales=False,
        use_ue8m0=use_ue8m0,
    )

    # 1. Test native implementation (always available)
    x_quant_native, scales_native = quant_op.forward_native(x.clone())
    assert x_quant_native.shape == x.shape
    assert scales_native.shape == (batch_size, expected_num_groups)

    # 2. Test column-major scales configuration
    quant_op_col = QuantFP8(
        static=False,
        group_shape=group_shape,
        column_major_scales=True,
        use_ue8m0=use_ue8m0,
    )
    _, scales_col = quant_op_col.forward_native(x.clone())
    assert scales_col.shape == (batch_size, expected_num_groups)
    assert scales_col.stride(0) == 1
    assert scales_col.stride(1) == batch_size

    # Test column-major scales consistency
    torch.testing.assert_close(scales_col, scales_native, rtol=1e-9, atol=1e-8)

    # 3. Test CUDA implementation (only for divisible dimensions)
    if is_divisible:
        x_quant_cuda, scales_cuda = quant_op.forward_cuda(x.clone())
        assert x_quant_cuda.shape == x.shape
        assert scales_cuda.shape == (batch_size, expected_num_groups)

        # Verify CUDA/native consistency
        torch.testing.assert_close(scales_cuda, scales_native, rtol=2e-7, atol=2e-8)

        # Quantized values should mostly match
        diff_count = (x_quant_cuda != x_quant_native).sum().item()
        diff_ratio = diff_count / x_quant_cuda.numel()
        assert diff_ratio < 0.002, f"Too many differences: {diff_ratio:.4%}"