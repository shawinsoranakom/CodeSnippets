def test_cutlass_fp8_group_gemm(
    num_experts: int, per_act_token: bool, per_out_ch: bool, use_bias: bool
):
    # Device and dtype setup
    device = "cuda"
    out_dtype = torch.half

    # Create separate A, B, C tensors for each group
    a_tensors = []
    b_tensors = []
    a_scales_tensors = []
    b_scales_tensors = []
    baseline_tensors = []

    expert_offsets = torch.zeros((num_experts + 1), device=device, dtype=torch.int64)

    problem_sizes = torch.zeros((num_experts, 3), device=device, dtype=torch.int32)

    if not per_act_token:
        one_scale_a = torch.randn((1, 1), device=device, dtype=torch.float32)

    alignment = 16  # 128 // 8
    # For variation, each group has dimensions
    n_g = alignment * random.randint(1, 64)
    k_g = alignment * random.randint(1, 64)
    for g in range(num_experts):
        m_g = alignment * random.randint(1, 64)

        expert_offsets[g + 1] = expert_offsets[g] + m_g
        problem_sizes[g][0] = m_g
        problem_sizes[g][1] = n_g
        problem_sizes[g][2] = k_g

        m_a_scales = m_g if per_act_token else 1
        n_b_scales = n_g if per_out_ch else 1

        # Create group-specific A and B (FP8) and output (FP16/FP32)
        a_g = to_fp8(torch.randn((m_g, k_g), device=device))
        b_g = to_fp8(torch.randn((n_g, k_g), device=device).t())
        a_tensors.append(a_g)
        b_tensors.append(b_g)

        # Set up A/B scales
        scale_b = torch.randn((1, n_b_scales), device=device, dtype=torch.float32)
        b_scales_tensors.append(scale_b)

        if per_act_token:
            scale_a = torch.randn((m_a_scales, 1), device=device, dtype=torch.float32)
            a_scales_tensors.append(scale_a)
        else:
            scale_a = one_scale_a

        # Compute baseline result for this group
        baseline_g = baseline_scaled_mm(a_g, b_g, scale_a, scale_b, out_dtype, None)
        baseline_tensors.append(baseline_g)

    a_tensors_stacked = torch.empty(
        (expert_offsets[num_experts], k_g), device=device, dtype=torch.float8_e4m3fn
    )
    b_tensors_stacked = torch.empty(
        (num_experts, n_g, k_g), device=device, dtype=torch.float8_e4m3fn
    )

    for g in range(num_experts):
        a_tensors_stacked[expert_offsets[g] : expert_offsets[g + 1]] = a_tensors[g]
        b_tensors_stacked[g] = b_tensors[g].t()
    b_tensors_stacked = b_tensors_stacked.transpose(1, 2)

    if per_act_token:
        a_scales_tensors_stacked = torch.empty(
            (expert_offsets[num_experts], 1), device=device, dtype=torch.float32
        )
        for g in range(num_experts):
            a_scales_tensors_stacked[expert_offsets[g] : expert_offsets[g + 1]] = (
                a_scales_tensors[g]
            )
    else:
        a_scales_tensors_stacked = one_scale_a

    b_scales_tensors_stacked = torch.empty(
        (num_experts, n_b_scales), device=device, dtype=torch.float32
    )
    for g in range(num_experts):
        b_scales_tensors_stacked[g] = b_scales_tensors[g]

    out_tensors_stacked = torch.zeros(
        (expert_offsets[num_experts], n_g), device=device, dtype=out_dtype
    )

    ab_strides = torch.full(
        (num_experts,), a_tensors_stacked.stride(0), device="cuda", dtype=torch.int64
    )
    c_strides = torch.full(
        (num_experts,), out_tensors_stacked.stride(0), device="cuda", dtype=torch.int64
    )

    ops.cutlass_moe_mm(
        out_tensors_stacked,
        a_tensors_stacked,
        b_tensors_stacked,
        a_scales_tensors_stacked,
        b_scales_tensors_stacked,
        expert_offsets[:-1],
        problem_sizes,
        ab_strides,
        ab_strides,
        c_strides,
        per_act_token,
        per_out_ch,
    )

    # Validate each group's result against the baseline
    for g in range(num_experts):
        baseline = baseline_tensors[g]
        c = out_tensors_stacked[expert_offsets[g] : expert_offsets[g + 1]]
        torch.testing.assert_close(c, baseline, rtol=1e-2, atol=5e-4)