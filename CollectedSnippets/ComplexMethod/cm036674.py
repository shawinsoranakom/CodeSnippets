def test_gptq_marlin_repack(
    k_chunk, n_chunk, quant_type, act_order, is_a_8bit, nk_factors
):
    n_factor, k_factor = nk_factors

    size_k = k_chunk * k_factor
    size_n = n_chunk * n_factor
    group_size = 128

    # Filter act_order
    if act_order:
        if group_size == -1:
            return
        if group_size == size_k:
            return
        if is_a_8bit:
            return

    # Normalize group_size
    if group_size == -1:
        group_size = size_k
    assert group_size <= size_k

    # Create input
    b_weight = rand_data((size_k, size_n))

    # Quantize (and apply act_order if provided)
    w_ref, q_w, s, g_idx, rand_perm = gptq_quantize_weights(
        b_weight, quant_type, group_size, act_order
    )

    # Pack to GPTQ format
    q_w_gptq = gptq_pack(q_w, quant_type.size_bits, size_k, size_n)

    # For act_order, sort the "weights" and "g_idx" so that group ids are
    # increasing
    sort_indices = torch.empty(0, dtype=torch.int, device=b_weight.device)
    if act_order:
        q_w, g_idx, sort_indices = sort_weights(q_w, g_idx)

    # Pack to Marlin format
    weight_perm = get_weight_perm(quant_type.size_bits, is_a_8bit)
    marlin_q_w_1 = marlin_weights(
        q_w, size_k, size_n, quant_type.size_bits, weight_perm, is_a_8bit
    )

    opcheck(
        torch.ops._C.gptq_marlin_repack,
        (q_w_gptq, sort_indices, size_k, size_n, quant_type.size_bits, is_a_8bit),
    )

    # Run Marlin repack GPU kernel
    marlin_q_w_2 = ops.gptq_marlin_repack(
        q_w_gptq, sort_indices, size_k, size_n, quant_type.size_bits, is_a_8bit
    )
    torch.accelerator.synchronize()

    torch.testing.assert_close(marlin_q_w_1, marlin_q_w_2)