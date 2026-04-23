def test_marlin_gemm(
    a_type,
    b_type,
    c_type,
    group_blocks,
    size_m,
    size_n,
    size_k,
    act_order,
    is_k_full,
    use_atomic_add,
    use_fp32_reduce,
):
    has_zp = b_type in [scalar_types.uint4, scalar_types.uint8]

    group_size = group_blocks if group_blocks <= 0 else group_blocks * 16

    if c_type == scalar_types.float16:
        dtype = torch.float16
    elif c_type == scalar_types.bfloat16:
        dtype = torch.bfloat16
    else:
        raise RuntimeError("unsupported c_type")

    if a_type == scalar_types.int8:
        a_dtype = torch.int8
    elif a_type == scalar_types.float8_e4m3fn:
        a_dtype = torch.float8_e4m3fn
    else:
        a_dtype = dtype

    a_input = rand_data((size_m, size_k), dtype=dtype)
    b_weight = rand_data((size_k, size_n), dtype=dtype)

    if b_type == scalar_types.float4_e2m1f:
        if group_size == 16:
            w_ref, marlin_q_w, marlin_s, marlin_s2 = rand_marlin_weight_nvfp4_like(
                b_weight.T, group_size, input_dtype=a_dtype
            )
        else:
            w_ref, marlin_q_w, marlin_s = rand_marlin_weight_mxfp4_like(
                b_weight.T, group_size, input_dtype=a_dtype
            )
            marlin_s2 = None

        g_idx = None
        sort_indices = None
        marlin_zp = None
    elif b_type == scalar_types.float8_e4m3fn:
        w_ref, marlin_q_w, marlin_s = marlin_quant_fp8_torch(
            b_weight.T, group_size, input_dtype=a_dtype
        )
        g_idx = None
        sort_indices = None
        marlin_zp = None
        marlin_s2 = None
    elif has_zp:
        w_ref, marlin_q_w, marlin_s, marlin_zp = awq_marlin_quantize(
            b_weight, b_type, group_size, input_dtype=a_dtype
        )
        g_idx = None
        sort_indices = None
        marlin_s2 = None
    else:
        w_ref, marlin_q_w, marlin_s, g_idx, sort_indices, _ = marlin_quantize(
            b_weight, b_type, group_size, act_order, input_dtype=a_dtype
        )

        marlin_zp = None
        marlin_s2 = None

    workspace = marlin_make_workspace_new(w_ref.device)

    if a_type == scalar_types.int8:
        a_input, a_scales = per_token_quant_int8(a_input)
        a_input_ref = a_input.to(a_scales.dtype) * a_scales.view(-1, 1)
        a_input_ref = a_input_ref.to(dtype)

        if group_size != -1:
            a_scales = a_scales / 4096 * marlin_s.max()
            a_scales = a_scales.float()
            marlin_s = marlin_s / marlin_s.max() * 4096
            marlin_s = marlin_s.round().to(torch.int16).view(dtype)
    elif a_type == scalar_types.float8_e4m3fn:
        a_input, a_scales = ops.scaled_fp8_quant(a_input, use_per_token_if_dynamic=True)
        a_input_ref = a_input.to(a_scales.dtype) * a_scales.view(-1, 1)
        a_input_ref = a_input_ref.to(dtype)
    else:
        assert a_type.size_bits == 16
        a_input_ref = a_input
        a_scales = None

    output = torch.empty((size_m, size_n), dtype=dtype, device=a_input.device)

    output = ops.marlin_gemm(
        a_input,
        output,
        marlin_q_w,
        None,
        marlin_s,
        a_scales,
        marlin_s2,
        marlin_zp,
        g_idx,
        sort_indices,
        workspace,
        b_type,
        a_input.shape[0],
        b_weight.shape[1],
        a_input.shape[1],
        is_k_full=is_k_full,
        use_atomic_add=use_atomic_add,
        use_fp32_reduce=use_fp32_reduce,
        is_zp_float=False,
    )
    output_ref = torch.matmul(a_input_ref, w_ref)

    max_diff = compute_max_diff(output, output_ref)
    assert max_diff < 0.04