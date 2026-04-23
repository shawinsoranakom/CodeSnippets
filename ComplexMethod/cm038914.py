def gen_marlin_params():
        # Marlin quant
        marlin_g_idx = marlin_sort_indices = marlin_zp = marlin_s2 = None
        if quant_type == scalar_types.float4_e2m1f:
            if group_size != 16 or act_order:
                return
            marlin_w_ref, marlin_q_w, marlin_s, marlin_s2 = rand_marlin_weight_fp4_like(
                b.T, group_size
            )
        elif quant_type == scalar_types.float8_e4m3fn:
            if group_size not in [-1, 128] or act_order:
                return
            marlin_w_ref, marlin_q_w, marlin_s = marlin_quant_fp8_torch(b.T, group_size)
        elif group_size == 16:
            return
        elif has_zp:
            marlin_w_ref, marlin_q_w, marlin_s, marlin_zp = awq_marlin_quantize(
                b, quant_type, group_size
            )
        else:
            marlin_w_ref, marlin_q_w, marlin_s, marlin_g_idx, marlin_sort_indices, _ = (
                marlin_quantize(b, quant_type, group_size, act_order)
            )
        return (
            marlin_w_ref,
            marlin_q_w,
            marlin_s,
            marlin_s2,
            marlin_zp,
            marlin_g_idx,
            marlin_sort_indices,
        )