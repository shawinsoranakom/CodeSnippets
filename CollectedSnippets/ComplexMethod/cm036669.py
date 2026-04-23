def test_fused_post_conv_correctness(H, HV, K, V, L, apply_l2norm, output_g_exp, dtype):
    """Test fused kernel matches reference for all configs."""
    torch.manual_seed(42)
    device = "cuda"
    qkv_dim = 2 * H * K + HV * V

    conv_output = torch.randn(L, qkv_dim, dtype=dtype, device=device)
    a = torch.randn(L, HV, dtype=dtype, device=device)
    b = torch.randn(L, HV, dtype=dtype, device=device)
    A_log = torch.randn(HV, dtype=torch.float32, device=device) - 2.0
    dt_bias = torch.randn(HV, dtype=torch.float32, device=device) * 0.1

    # Reference
    ref_q, ref_k, ref_v, ref_g, ref_beta = reference_post_conv(
        conv_output,
        a,
        b,
        A_log,
        dt_bias,
        H,
        K,
        V,
        apply_l2norm,
        output_g_exp,
    )

    # Fused kernel
    fused_q, fused_k, fused_v, fused_g, fused_beta = fused_post_conv_prep(
        conv_output,
        a,
        b,
        A_log,
        dt_bias,
        num_k_heads=H,
        head_k_dim=K,
        head_v_dim=V,
        apply_l2norm=apply_l2norm,
        output_g_exp=output_g_exp,
    )

    # Check shapes
    assert fused_q.shape == (L, H, K), f"q shape: {fused_q.shape}"
    assert fused_k.shape == (L, H, K), f"k shape: {fused_k.shape}"
    assert fused_v.shape == (L, HV, V), f"v shape: {fused_v.shape}"
    assert fused_g.shape == (L, HV), f"g shape: {fused_g.shape}"
    assert fused_beta.shape == (L, HV), f"beta shape: {fused_beta.shape}"

    # Check dtypes
    assert fused_q.dtype == dtype
    assert fused_k.dtype == dtype
    assert fused_v.dtype == dtype
    assert fused_g.dtype == torch.float32
    assert fused_beta.dtype == torch.float32

    # Check contiguity
    assert fused_q.is_contiguous()
    assert fused_k.is_contiguous()
    assert fused_v.is_contiguous()

    # Check values
    atol_qkv = 1e-2 if apply_l2norm else 1e-3
    rtol_qkv = 1e-2 if apply_l2norm else 1e-3

    torch.testing.assert_close(fused_q, ref_q, atol=atol_qkv, rtol=rtol_qkv)
    torch.testing.assert_close(fused_k, ref_k, atol=atol_qkv, rtol=rtol_qkv)
    torch.testing.assert_close(fused_v, ref_v, atol=1e-3, rtol=1e-3)
    torch.testing.assert_close(fused_g, ref_g, atol=1e-4, rtol=1e-4)
    torch.testing.assert_close(fused_beta, ref_beta, atol=1e-4, rtol=1e-4)