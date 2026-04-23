def marlin_quantize(
    w: torch.Tensor,
    quant_type: ScalarType,
    group_size: int,
    act_order: bool,
    test_perm: torch.Tensor | None = None,
    input_dtype: torch.dtype | None = None,
):
    is_a_8bit = input_dtype is not None and input_dtype.itemsize == 1

    size_k, size_n = w.shape
    num_bits = quant_type.size_bits

    # Normalize group_size
    if group_size == -1:
        group_size = size_k
    assert group_size <= size_k

    # Quantize (and apply act_order if provided)
    w_ref, q_w, s, g_idx, rand_perm = gptq_quantize_weights(
        w, quant_type, group_size, act_order, test_perm
    )

    # For act_order, sort the "weights" and "g_idx" so that group ids are
    # increasing
    sort_indices = torch.empty(0, dtype=torch.int, device=w.device)
    if act_order:
        q_w, g_idx, sort_indices = sort_weights(q_w, g_idx)

    # Reformat to marlin
    weight_perm = get_weight_perm(num_bits, is_a_8bit)
    marlin_q_w = marlin_weights(
        q_w, size_k, size_n, num_bits, weight_perm, is_a_8bit=is_a_8bit
    )
    marlin_s = marlin_permute_scales(s, size_k, size_n, group_size, is_a_8bit=is_a_8bit)

    if input_dtype == torch.float8_e4m3fn and quant_type == scalar_types.uint4b8:
        ops.marlin_int4_fp8_preprocess(marlin_q_w, inplace=True)
        marlin_s = marlin_s * 512

    # Create result
    res_list = [w_ref, marlin_q_w, marlin_s, g_idx, sort_indices, rand_perm]
    for i in range(len(res_list)):
        res_list[i] = res_list[i].to(w.device)

    return res_list