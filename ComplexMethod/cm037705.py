def prepare_moe_fp4_layer_for_marlin(
    layer: torch.nn.Module, input_dtype: torch.dtype | None = None
) -> None:
    is_nvfp4 = hasattr(layer, "w13_weight_scale_2")
    if input_dtype is not None and input_dtype.itemsize == 1:
        if is_nvfp4:
            raise RuntimeError("NVFP4 weight + INT8/FP8 activation is not supported.")
        elif input_dtype != torch.float8_e4m3fn:
            raise RuntimeError("MXFP4 weight + INT8 activation is not supported.")

    group_size = 16 if is_nvfp4 else 32

    e = layer.moe_config.num_experts
    k = layer.moe_config.hidden_dim
    n = layer.moe_config.intermediate_size_per_partition

    # WORKSPACE
    device = layer.w13_weight.device
    param_dtype = layer.params_dtype
    layer.workspace = marlin_make_workspace_new(device, 4)
    perm = torch.empty(0, dtype=torch.int, device=device)
    is_a_8bit = input_dtype is not None and input_dtype.itemsize == 1

    # WEIGHT
    # Repack weights to marlin format
    for name in ["w13_weight", "w2_weight"]:
        weight = getattr(layer, name)
        tensor_list = []
        if "w13" in name:
            size_n, size_k = n * 2, k
        else:
            size_n, size_k = k, n

        assert weight.shape == (e, size_n, size_k // 2)

        for i in range(e):
            qweight = weight[i].view(torch.int32).T.contiguous()

            marlin_qweight = ops.gptq_marlin_repack(
                b_q_weight=qweight,
                perm=perm,
                size_k=size_k,
                size_n=size_n,
                num_bits=4,
                is_a_8bit=is_a_8bit,
            )
            tensor_list.append(marlin_qweight)

        weight = torch.cat([x.unsqueeze(0) for x in tensor_list], 0)
        weight = torch.nn.Parameter(weight, requires_grad=False)

        setattr(layer, name, weight)

    # WEIGHT SCALES
    # Permute scales
    for name in ["w13", "w2"]:
        scales = getattr(layer, name + "_weight_scale")
        if not is_nvfp4:
            scales = scales.view(torch.float8_e8m0fnu)
        scales = scales.to(param_dtype)
        if is_nvfp4:
            global_scale = getattr(layer, name + "_weight_scale_2")

        tensor_list = []
        if "w13" in name:
            size_n, size_k = n * 2, k
        else:
            size_n, size_k = k, n

        # For NVFP4: compute unified scale_factor across all experts
        combined_scale_factor = None
        if is_nvfp4:
            combined_scale_factor = _nvfp4_compute_scale_factor(scales, param_dtype)

        for i in range(e):
            scale = scales[i].T

            marlin_scales = marlin_permute_scales(
                s=scale,
                size_k=size_k,
                size_n=size_n,
                group_size=group_size,
                is_a_8bit=is_a_8bit,
            )
            if is_nvfp4:
                marlin_scales, _ = nvfp4_marlin_process_scales(
                    marlin_scales,
                    scale_factor=combined_scale_factor,
                    a_dtype=param_dtype,
                )
            else:
                marlin_scales = mxfp4_marlin_process_scales(
                    marlin_scales, input_dtype=input_dtype
                )
            tensor_list.append(marlin_scales)

        scales = torch.cat([x.unsqueeze(0) for x in tensor_list], 0)
        scales = torch.nn.Parameter(scales, requires_grad=False)
        setattr(layer, name + "_weight_scale", scales)

        if is_nvfp4:
            assert combined_scale_factor is not None
            global_scale = nvfp4_marlin_process_global_scale(global_scale, param_dtype)
            global_scale = global_scale / combined_scale_factor
            global_scale = torch.nn.Parameter(global_scale, requires_grad=False)
            setattr(layer, name + "_weight_scale_2", global_scale)

    # BIAS
    # Permute bias
    for name in ["w13_bias", "w2_bias"]:
        if not hasattr(layer, name):
            continue
        bias = getattr(layer, name).to(param_dtype)

        tensor_list = []
        for i in range(e):
            expert_bias = bias[i]

            tensor_list.append(marlin_permute_bias(expert_bias))

        bias = torch.cat([x.unsqueeze(0) for x in tensor_list], 0)
        bias = torch.nn.Parameter(bias, requires_grad=False)
        setattr(layer, name, bias)