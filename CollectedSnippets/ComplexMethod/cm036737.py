def make(
        w: torch.Tensor,
        quant_type: ScalarType,
        group_size: int,
        act_order: bool | None = None,
        bias: torch.Tensor | None = None,
        input_type: ScalarType = None,
    ) -> "MarlinMoEWeightData":
        assert w.ndim == 3

        has_zp = quant_type in [scalar_types.uint4, scalar_types.uint8]
        k = w.shape[-1]

        if input_type == scalar_types.int8:
            input_dtype = torch.int8
        elif input_type == scalar_types.float8_e4m3fn:
            input_dtype = torch.float8_e4m3fn
        else:
            input_dtype = w.dtype

        w_ref_l: list[torch.Tensor] = []
        qweight_l: list[torch.Tensor] = []
        scales_l: list[torch.Tensor] = []
        global_scale_l: list[torch.Tensor] = []
        zeros_l: list[torch.Tensor] = []
        g_idx_l: list[torch.Tensor] = []
        sort_indices_l: list[torch.Tensor] = []
        bias_l: list[torch.Tensor] = []

        for i in range(w.shape[0]):
            if quant_type == scalar_types.float4_e2m1f:
                if group_size == 16:
                    w_ref, qweight, scales, global_scale = (
                        rand_marlin_weight_nvfp4_like(
                            w[i], group_size, input_dtype=input_dtype
                        )
                    )
                else:
                    w_ref, qweight, scales = rand_marlin_weight_mxfp4_like(
                        w[i], group_size, input_dtype=input_dtype
                    )
                    global_scale = None

                w_ref_l.append(w_ref.T)
                qweight_l.append(qweight)
                scales_l.append(scales)
                if global_scale is not None:
                    global_scale_l.append(global_scale)
            elif quant_type == scalar_types.float8_e4m3fn:
                w_ref, qweight, scales = marlin_quant_fp8_torch(
                    w[i], group_size, input_dtype=input_dtype
                )
                w_ref_l.append(w_ref.T)
                qweight_l.append(qweight)
                scales_l.append(scales)
            elif has_zp:
                w_ref, qweight, scales, zeros = awq_marlin_quantize(
                    w[i].transpose(1, 0),
                    quant_type,
                    group_size,
                    input_dtype=input_dtype,
                )

                w_ref_l.append(w_ref.T)
                qweight_l.append(qweight)
                scales_l.append(scales)
                zeros_l.append(zeros)
            else:
                test_perm = torch.randperm(k)
                w_ref, qweight, scales, g_idx, sort_indices, _ = marlin_quantize(
                    w[i].transpose(1, 0),
                    quant_type,
                    group_size,
                    act_order,
                    test_perm,
                    input_dtype=input_dtype,
                )

                w_ref_l.append(w_ref.T)
                qweight_l.append(qweight)
                scales_l.append(scales)
                g_idx_l.append(g_idx)
                sort_indices_l.append(sort_indices)

            if bias is not None:
                bias_l.append(marlin_permute_bias(bias[i]))

        w_ref = stack_and_dev(w_ref_l)
        qweight = stack_and_dev(qweight_l).contiguous()
        scales = stack_and_dev(scales_l)
        global_scale = stack_and_dev(global_scale_l) if global_scale_l else None
        g_idx = stack_and_dev(g_idx_l) if g_idx_l else None
        zeros = stack_and_dev(zeros_l) if zeros_l else None
        sort_indices = stack_and_dev(sort_indices_l) if sort_indices_l else None
        marlin_bias = stack_and_dev(bias_l) if bias_l else None

        a_scales_factor = None
        if input_type == scalar_types.int8 and group_size != -1:
            a_scales_factor = 1 / 4096 * scales.max().float()
            scales = scales / scales.max() * 4096
            scales = scales.round().to(torch.int16).view(w.dtype)

        return MarlinMoEWeightData(
            w_ref=w_ref,
            qweight=qweight,
            scales=scales,
            global_scale=global_scale,
            a_scales_factor=a_scales_factor,
            g_idx=g_idx,
            zeros=zeros,
            sort_indices=sort_indices,
            marlin_bias=marlin_bias,
        )