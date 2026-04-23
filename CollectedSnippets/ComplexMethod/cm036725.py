def test_cutlass_mxfp4_grouped_mm(num_experts, out_dtype):
    """
    Test the MXFP4 grouped GEMM kernel by:
    1. Creating random per-expert inputs and weights
    2. Quantizing both to MXFP4 using the CUDA kernel
    3. Running the CUTLASS grouped GEMM
    4. Comparing against BF16 reference
    """
    device = "cuda"
    alignment = 128
    # N and K must be multiples of 128 for clean swizzle layout
    n_g = random.randint(1, 16) * alignment
    k_g = random.randint(1, 16) * alignment

    expert_offset = 0
    expert_offsets_input = []
    problem_sizes = []
    input_list = []
    weight_list = []

    for g in range(num_experts):
        m_g = random.randint(1, 256)
        expert_offsets_input.append(expert_offset)
        expert_offset += m_g
        problem_sizes.append([m_g, n_g, k_g])

        input_list.append(
            torch.normal(0.0, std=0.5, size=(m_g, k_g), device=device, dtype=out_dtype)
        )
        weight_list.append(
            torch.normal(0.0, std=0.5, size=(n_g, k_g), device=device, dtype=out_dtype)
        )

    input_tensor = torch.concat(input_list, dim=0)  # [M_total, K]

    # --- Quantize INPUTS via mxfp4_experts_quant ---
    input_bs_offsets = []
    tot = 0
    for g in range(num_experts):
        input_bs_offsets.append(tot)
        tot += align(problem_sizes[g][0], 128)
    input_bs_offsets.append(tot)

    _inp_expert_offsets = torch.tensor(
        expert_offsets_input + [expert_offset], device=device, dtype=torch.int32
    )
    _inp_bs_offsets = torch.tensor(input_bs_offsets, device=device, dtype=torch.int32)

    input_quant, input_sf = ops.mxfp4_experts_quant(
        input_tensor,
        _inp_expert_offsets,
        _inp_bs_offsets,
        num_experts,
        topk=1,
    )

    # --- Quantize WEIGHTS via mxfp4_experts_quant ---
    # Treat each expert's N weight rows as an "expert" with N tokens
    weight_tensor = torch.concat(weight_list, dim=0)  # [E*N, K]
    weight_expert_offsets = [g * n_g for g in range(num_experts)] + [num_experts * n_g]
    # N is always multiple of 128, so blockscale offsets are clean
    weight_bs_offsets = [g * n_g for g in range(num_experts)] + [num_experts * n_g]

    _wt_expert_offsets = torch.tensor(
        weight_expert_offsets, device=device, dtype=torch.int32
    )
    _wt_bs_offsets = torch.tensor(weight_bs_offsets, device=device, dtype=torch.int32)

    weight_quant, weight_sf = ops.mxfp4_experts_quant(
        weight_tensor,
        _wt_expert_offsets,
        _wt_bs_offsets,
        num_experts,
        topk=1,
    )

    # Reshape weight quantized data to [E, N, K//2]
    weight_quant = weight_quant[: num_experts * n_g].view(num_experts, n_g, k_g // 2)

    # Reshape weight scale factors to [E, N, K//32]
    # The quant kernel produces uint8 SF buffer. Each row has K//32 SFs.
    scales_per_row = k_g // MXFP4_BLOCK_SIZE
    weight_sf_flat = weight_sf.view(-1)[: num_experts * n_g * scales_per_row]
    weight_sf_3d = weight_sf_flat.view(num_experts, n_g, scales_per_row)

    # Output
    output = torch.empty((expert_offset, n_g), device=device, dtype=out_dtype)

    _problem_sizes = torch.tensor(problem_sizes, device=device, dtype=torch.int32)
    _expert_offsets = torch.tensor(
        expert_offsets_input, device=device, dtype=torch.int32
    )
    _input_bs = torch.tensor(input_bs_offsets[:-1], device=device, dtype=torch.int32)

    # Run the MXFP4 grouped GEMM
    ops.cutlass_mxfp4_moe_mm(
        output,
        input_quant,
        weight_quant,
        input_sf,
        weight_sf_3d,
        _problem_sizes,
        _expert_offsets,
        _input_bs,
    )

    # Reference: BF16 matmul
    ref_output = compute_ref_output(
        input_tensor=input_tensor,
        weight_list=weight_list,
        expert_offsets=expert_offsets_input,
        expert_offset=expert_offset,
        num_experts=num_experts,
    )

    # Compare per-expert
    for g in range(num_experts):
        start = expert_offsets_input[g]
        end = expert_offsets_input[g + 1] if g + 1 < num_experts else expert_offset
        if start == end:
            continue
        baseline = ref_output[start:end]
        actual = output[start:end]
        diff = calc_diff(actual, baseline)
        print(
            f"m_g={end - start} n_g={n_g} k_g={k_g} "
            f"num_experts={num_experts}, "
            f"out_dtype={out_dtype}, diff={diff:.5f}"
        )
        # FP4 quantization is very lossy (~4 bits precision)
        # Comparing quantized vs full-precision gives cosine diff of 0.05-0.15
        assert diff < 0.15, f"Expert {g}: diff={diff:.5f} exceeds threshold"