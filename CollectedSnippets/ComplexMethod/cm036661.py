def test_layer_norm_fwd_with_groups(
    num_tokens: int,
    hidden_size: int,
    group_size: int,
    dtype: torch.dtype,
    is_rms_norm: bool,
) -> None:
    """Test layer norm forward pass with group normalization."""
    if hidden_size % group_size != 0:
        pytest.skip(
            f"hidden_size {hidden_size} not divisible by group_size {group_size}"
        )

    set_random_seed(42)
    device = torch.device("cuda:0")

    # Create inputs
    x = torch.randn(num_tokens, hidden_size, dtype=dtype, device=device)
    weight = torch.randn(hidden_size, dtype=dtype, device=device)
    bias = None if is_rms_norm else torch.randn(hidden_size, dtype=dtype, device=device)
    eps = 1e-6

    ngroups = hidden_size // group_size

    # Run the triton kernel
    out, mean, rstd = layer_norm_fwd(
        x, weight, bias, eps, z=None, group_size=group_size, is_rms_norm=is_rms_norm
    )

    # Run reference implementation
    ref_out = layer_norm_ref(
        x, weight, bias, z=None, eps=eps, group_size=group_size, is_rms_norm=is_rms_norm
    )

    # Check outputs
    assert out.shape == x.shape
    assert out.dtype == x.dtype
    torch.testing.assert_close(out, ref_out, atol=1e-2, rtol=1e-2)

    # Check mean and rstd shapes for groups
    if not is_rms_norm:
        assert mean.shape == (ngroups * num_tokens,)
    assert rstd.shape == (ngroups * num_tokens,)