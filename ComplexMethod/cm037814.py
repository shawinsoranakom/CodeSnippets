def flashinfer_cutedsl_moe_masked(
    hidden_states: torch.Tensor | tuple[torch.Tensor, torch.Tensor],
    input_global_scale: torch.Tensor,
    w1: torch.Tensor,
    w1_blockscale: torch.Tensor,
    w1_alpha,
    w2: torch.Tensor,
    a2_global_scale: torch.Tensor,
    w2_blockscale: torch.Tensor,
    w2_alpha,
    masked_m: torch.Tensor,
    workspace: torch.Tensor,
    out: torch.Tensor,
):
    """
    Perform masked Mixture-of-Experts computation with FlashInfer's CuteDSL
    kernels.

    Args:
        hidden_states: Either of the following case
            * torch.Tensor: [num_experts, m, k], bf16
            * tuple[torch.Tensor, torch.Tensor]: [num_experts, m, k // 2],
                  uint8, [num_experts, m, k // 16], float8_e4m3fn
        input_global_scale (torch.Tensor): (l,)
        w1 (torch.Tensor): fp4 weights, [l, 2 * n, k // 2], uint8
        w1_blockscale (torch.Tensor): blockscale factors, e4m3,
        w1_alpha (torch.Tensor): (l,)
        w2 (torch.Tensor): fp4 weights, [l, k, n // 2], uint8
        a2_global_scale (torch.Tensor): (l,)
        w2_blockscale (torch.Tensor): blockscale factors, e4m3,
        w2_alpha (torch.Tensor): (l,)
        masked_m (torch.Tensor): Masked dimension indices
        workspace (torch.Tensor): For gateup_output

    Notes:
        - Assumes max(masked_m) <= m.
    """

    # === Assertions on dtypes ===
    assert w1.dtype == torch.uint8, f"w1 must be uint8, got {w1.dtype}"
    assert w1_blockscale.dtype == torch.float8_e4m3fn, (
        f"w1_blockscale must be float8_e4m3fn, got {w1_blockscale.dtype}"
    )
    assert w1_alpha.dtype == torch.float32, (
        f"w1_alpha must be float32, got {w1_alpha.dtype}"
    )
    assert w2.dtype == torch.uint8, f"w2 must be uint8, got {w2.dtype}"
    assert a2_global_scale.dtype == torch.float32, (
        f"a2_global_scale must be float32, got {a2_global_scale.dtype}"
    )
    assert w2_blockscale.dtype == torch.float8_e4m3fn, (
        f"w2_blockscale must be float8_e4m3fn, got {w2_blockscale.dtype}"
    )
    assert w2_alpha.dtype == torch.float32, (
        f"w2_alpha must be float32, got {w2_alpha.dtype}"
    )

    # === Assertions on shapes ===
    n = w2.shape[-1] * 2  # intermediate dimension
    if isinstance(hidden_states, tuple):
        assert input_global_scale is None, (
            "input_global_scale is needed when input needs quant"
        )

        aq = hidden_states[0].view(torch.uint8)
        aq_sf = hidden_states[1].view(torch.float8_e4m3fn)
        # m, k_by_2, num_experts = aq.shape
        num_experts, m, k_by_2 = aq.shape
        k = k_by_2 * 2
        aq = aq.permute(1, 2, 0)
    else:
        num_experts, m, k = hidden_states.shape

        assert input_global_scale.dtype == torch.float32, (
            f"input_global_scale must be float32, got {input_global_scale.dtype}"
        )
        assert input_global_scale.shape == (num_experts,), (
            f"input_global_scale must be (l,), got {input_global_scale.shape}"
        )

        aq, aq_sf = scaled_fp4_grouped_quantize(
            hidden_states,
            masked_m,
            input_global_scale,
        )

    assert w1.shape[-2] == 2 * n, f"w1 last-2 dim must be 2*n, got {w1.shape}"
    assert w1.shape[-1] * 2 == k, (
        f"w1 last dim * 2 must equal k, got {w1.shape[-1]} vs k={k}"
    )
    assert w2.shape[-2:] == (
        k,
        n // 2,
    ), f"w2 shape mismatch, got {w2.shape[-2:]}, expected {(k, n // 2)}"

    assert w1_alpha.shape == (num_experts,), (
        f"w1_alpha must be (l,), got {w1_alpha.shape}"
    )
    assert a2_global_scale.shape == (num_experts,), (
        f"a2_global_scale must be (l,), got {a2_global_scale.shape}"
    )
    assert w2_alpha.shape == (num_experts,), (
        f"w2_alpha must be (l,), got {w2_alpha.shape}"
    )

    workspace = workspace.permute(1, 2, 0)  # requirement of kernel
    sf_vec_size = 16
    assert aq_sf.dtype == torch.float8_e4m3fn
    assert aq.dtype == torch.uint8
    ab_dtype = "float4_e2m1fn"
    sf_dtype = "float8_e4m3fn"

    if isinstance(hidden_states, tuple):
        c_dtype = "bfloat16"
    else:
        c_dtype = get_cute_dtype(hidden_states)

    # Gemm1
    flashinfer_cutedsl_grouped_gemm_nt_masked(
        (aq, aq_sf),
        (w1.permute(1, 2, 0), w1_blockscale),
        workspace,
        masked_m,
        ab_dtype=ab_dtype,
        sf_dtype=sf_dtype,
        c_dtype=c_dtype,
        sf_vec_size=sf_vec_size,
        alpha=w1_alpha.view(1, 1, num_experts),
        alpha_dtype=get_cute_dtype(w1_alpha),
    )  # in logical [m, n, l]

    # SILU and quantization
    diq, diq_sf = silu_and_mul_scaled_nvfp4_experts_quantize(
        workspace.permute(2, 0, 1),
        masked_m,
        a2_global_scale,
    )

    # Gemm2
    out = out.permute(1, 2, 0)  # requirement of kernel
    flashinfer_cutedsl_grouped_gemm_nt_masked(
        (diq, diq_sf),
        (w2.permute(1, 2, 0), w2_blockscale),
        out,
        masked_m,
        ab_dtype=ab_dtype,
        sf_dtype=sf_dtype,
        c_dtype=c_dtype,
        sf_vec_size=sf_vec_size,
        alpha=w2_alpha.view(1, 1, num_experts),
        alpha_dtype=get_cute_dtype(w2_alpha),
    )  # in logical [m, k, l]
    out = out.permute(2, 0, 1)