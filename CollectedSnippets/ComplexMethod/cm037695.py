def awq_marlin_quantize(
    w: torch.Tensor,
    quant_type: ScalarType,
    group_size: int,
    input_dtype: torch.dtype | None = None,
):
    is_a_8bit = input_dtype is not None and input_dtype.itemsize == 1
    size_k, size_n = w.shape

    # Normalize group_size
    if group_size == -1:
        group_size = size_k
    assert group_size <= size_k

    # Detect num groups
    assert size_k % group_size == 0
    num_groups = size_k // group_size

    # Quantize with zp
    w_ref, q_w, s, zp = quantize_weights(w, quant_type, group_size, zero_points=True)

    if input_dtype == torch.float8_e4m3fn and quant_type == scalar_types.uint4:
        repeated_zp = zp.repeat_interleave(group_size, 0)
        q_w_old = q_w
        q_w = q_w_old - repeated_zp
        q_w[q_w < 0] = 15 - q_w_old[q_w < 0]
        s = s * 512

    # Reformat to marlin
    weight_perm = get_weight_perm(quant_type.size_bits, is_a_8bit)
    marlin_q_w = marlin_weights(
        q_w, size_k, size_n, quant_type.size_bits, weight_perm, is_a_8bit=is_a_8bit
    )
    marlin_s = marlin_permute_scales(s, size_k, size_n, group_size, is_a_8bit=is_a_8bit)
    marlin_zp = marlin_zero_points(
        zp, num_groups, size_n, quant_type.size_bits, is_a_8bit=is_a_8bit
    )

    # Create result
    res_list = [w_ref, marlin_q_w, marlin_s, marlin_zp]
    for i in range(len(res_list)):
        res_list[i] = res_list[i].to(w.device)

    return res_list