def test_rms_norm(
    default_vllm_config,
    num_tokens: int,
    hidden_size: int,
    add_residual: bool,
    has_scale_ub: bool,
    dtype: torch.dtype,
    quant_dtype: torch.dtype,
    group_size: list[int] | None,
    tma_alignment: int,
    seed: int,
    device: str,
    strided_input: bool,
) -> None:
    set_random_seed(seed)
    torch.set_default_device(device)
    torch.accelerator.set_device_index(device)

    if group_size is not None and hidden_size % group_size[1] != 0:
        # skip
        pytest.skip("Skip non-divisible group sizes")

    if group_size is not None and has_scale_ub:
        # blockwise baseline doesn't support scale_ub
        pytest.skip("scale_ub not supported for blockwise/group quantization")

    if (
        group_size is None or quant_dtype != current_platform.fp8_dtype()
    ) and tma_alignment != 0:
        # TMA alignment is only supported for groupwise fp8 kernels
        pytest.skip("tma alignment not supported for per-token or int8 quantization")

    if (
        group_size is not None
        and tma_alignment != 0
        and hidden_size // group_size[1] % tma_alignment == 0
    ):
        # Skip tests where TMA alignment doesn't create extra padding to save time
        pytest.skip("Skip TMA alignment cases where no extra padding is added")

    if has_scale_ub and quant_dtype != current_platform.fp8_dtype():
        # skip
        pytest.skip("scale_ub only supported for fp8 quantization")

    layer = RMSNorm(hidden_size, EPS).to(dtype=dtype)

    # Make weights
    layer.weight.data.normal_(mean=1.0, std=0.1)

    # Make inputs: use a wider tensor and slice to create a non-contiguous
    # (strided) input when strided_input=True. The last dimension stride
    # remains 1, which the kernel requires.
    scale = 1 / (hidden_size)
    last_dim = 2 * hidden_size if strided_input else hidden_size
    x = torch.randn(num_tokens, last_dim, dtype=dtype) * scale
    x = x[:, :hidden_size]

    # dim 1 gets special-cased
    x_is_strided = strided_input and num_tokens != 1
    # check that the input is strided iff we expect it to be
    assert x.is_contiguous() != x_is_strided

    # Residual must still be contiguous
    residual = (
        torch.randn(num_tokens, hidden_size, dtype=dtype) * scale
        if add_residual
        else None
    )
    if has_scale_ub:
        rms_x, _ = ref_rms_norm(layer, x, residual)
        scale_ub = torch.mean(rms_x).to(dtype=torch.float32, device="cuda")
    else:
        scale_ub = None

    ref_out, ref_scales, ref_residual = ref_impl(
        layer, x, quant_dtype, residual, scale_ub, group_size
    )
    ops_out, ops_scales, ops_residual = ops_impl(
        layer.weight, x, quant_dtype, residual, scale_ub, group_size, tma_alignment
    )

    assert ref_out.dtype == quant_dtype
    assert ops_out.dtype == quant_dtype
    if quant_dtype == torch.int8:
        assert torch.allclose(ref_scales, ops_scales, atol=1e-6)
        # big atol to account for round-off errors.
        assert torch.allclose(ref_out, ops_out, atol=1)
    else:
        assert torch.allclose(ref_scales, ops_scales)
        a = ref_out.to(dtype=torch.float32)
        b = ops_out.to(dtype=torch.float32)
        ok = torch.allclose(a, b, atol=1e-6)
        if not ok:
            # fallback: compare dequantized values with relaxed tolerance
            if group_size is None:
                a_deq = a * ref_scales.view(-1, 1)
                b_deq = b * ops_scales.view(-1, 1)
            else:
                a_deq = a * ref_scales.repeat_interleave(group_size[1], dim=1)
                b_deq = b * ops_scales.repeat_interleave(group_size[1], dim=1)
            # NOTE: It is possible that some future test cases trigger this
            # max diff due to precision issues. If such an error is
            # encountered, it's recommended to inspect the differences between
            # all corresponding elements from each tensor (e.g. by looping over
            # them) and checking how many the max diff error shows up on (just
            # a few bad elements should still be considered acceptable).
            ok = torch.allclose(a_deq, b_deq, rtol=5e-2, atol=5e-2)
        assert ok
    if add_residual:
        assert torch.allclose(ref_residual, ops_residual)

    output = torch.empty(x.shape, dtype=quant_dtype, device=x.device)
    if group_size is None:
        scales = torch.empty(
            (x.numel() // x.shape[-1], 1), device=x.device, dtype=torch.float32
        )
        opcheck(
            torch.ops._C.rms_norm_dynamic_per_token_quant,
            (output, x, layer.weight, scales, 1e-5, scale_ub, residual),
        )
    else:
        assert hidden_size % group_size[1] == 0
        num_groups = hidden_size // group_size[1]
        scales = torch.empty(
            (num_groups, num_tokens),
            device=x.device,
            dtype=torch.float32,
        ).transpose(0, 1)
        opcheck(
            torch.ops._C.rms_norm_per_block_quant,
            (
                output,
                x,
                layer.weight,
                scales,
                1e-5,
                scale_ub,
                residual,
                group_size[1],
                True,  # is_scale_transposed
            ),
        )