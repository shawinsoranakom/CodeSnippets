def test_rocm_aiter_group_fp8_quant_torch_compile_with_cudagraph():
    """Test that rocm_aiter_ops.group_fp8_quant
    with group size 128 can be used with
    torch.compile in cudagraph mode."""
    # Create test tensors
    M = 128
    N = 4096
    group_size = 128

    input_tensor = torch.randn((M, N), dtype=torch.bfloat16, device="cuda")

    # Define a function that uses the op
    def group_fp8_quant_fn(x):
        return rocm_aiter_ops.group_fp8_quant(x, group_size)

    # Compile with cudagraph mode
    compiled_fn = torch.compile(
        group_fp8_quant_fn,
        fullgraph=True,
        backend="inductor",
        mode="reduce-overhead",
        dynamic=False,
    )

    # Run eager mode
    x_fp8_eager, scales_eager = group_fp8_quant_fn(input_tensor)

    # Run compiled version (first run will trigger compilation)
    x_fp8_compiled, scales_compiled = compiled_fn(input_tensor)

    # Verify shapes match
    assert x_fp8_compiled.shape == x_fp8_eager.shape
    assert scales_compiled.shape == scales_eager.shape

    # Verify expected shapes
    assert x_fp8_compiled.shape == (M, N)
    expected_scale_cols = (N + group_size - 1) // group_size
    assert scales_compiled.shape == (M, expected_scale_cols)

    # Verify results match
    assert torch.allclose(
        x_fp8_compiled.to(torch.float32),
        x_fp8_eager.to(torch.float32),
        rtol=1e-2,
        atol=1e-2,
    )
    assert torch.allclose(scales_compiled, scales_eager, rtol=1e-3, atol=1e-3)

    # Test with different input (reusing compiled graph)
    input_tensor_2 = torch.randn((M, N), dtype=torch.bfloat16, device="cuda")
    x_fp8_eager_2, scales_eager_2 = group_fp8_quant_fn(input_tensor_2)
    x_fp8_compiled_2, scales_compiled_2 = compiled_fn(input_tensor_2)

    # Verify second run also produces correct results
    assert torch.allclose(
        x_fp8_compiled_2.to(torch.float32),
        x_fp8_eager_2.to(torch.float32),
        rtol=1e-2,
        atol=1e-2,
    )
    assert torch.allclose(scales_compiled_2, scales_eager_2, rtol=1e-3, atol=1e-3)