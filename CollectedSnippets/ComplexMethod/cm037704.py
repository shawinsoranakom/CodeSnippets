def prepare_fp4_layer_for_marlin(
    layer: torch.nn.Module, input_dtype: torch.dtype | None = None
) -> None:
    is_nvfp4 = hasattr(layer, "weight_global_scale")
    if input_dtype is not None and input_dtype.itemsize == 1:
        if is_nvfp4:
            raise RuntimeError("NVFP4 weight + INT8/FP8 activation is not supported.")
        elif input_dtype != torch.float8_e4m3fn:
            raise RuntimeError("MXFP4 weight + INT8 activation is not supported.")

    group_size = 16 if is_nvfp4 else 32

    part_size_n = layer.output_size_per_partition
    part_size_k = layer.input_size_per_partition
    param_dtype = layer.params_dtype

    assert layer.weight.shape == (part_size_n, part_size_k // 2)

    device = layer.weight.device

    # WORKSPACE
    layer.workspace = marlin_make_workspace_new(device)

    # WEIGHT
    # Repack weights to marlin format
    perm = torch.empty(0, dtype=torch.int, device=device)
    qweight = layer.weight.view(torch.int32).T.contiguous()

    is_a_8bit = input_dtype is not None and input_dtype.itemsize == 1
    marlin_qweight = ops.gptq_marlin_repack(
        b_q_weight=qweight,
        perm=perm,
        size_k=part_size_k,
        size_n=part_size_n,
        num_bits=4,
        is_a_8bit=is_a_8bit,
    )
    layer.weight = torch.nn.Parameter(marlin_qweight, requires_grad=False)

    # WEIGHT SCALES
    # Permute scales
    weight_scale = layer.weight_scale.T.contiguous()

    if not is_nvfp4:
        weight_scale = weight_scale.view(torch.float8_e8m0fnu)

    weight_scale = weight_scale.to(param_dtype)
    weight_scale = marlin_permute_scales(
        s=weight_scale,
        size_k=part_size_k,
        size_n=part_size_n,
        group_size=group_size,
        is_a_8bit=is_a_8bit,
    )

    if is_nvfp4:
        weight_scale, scale_factor = nvfp4_marlin_process_scales(
            weight_scale, a_dtype=param_dtype
        )
        layer.weight_scale = torch.nn.Parameter(weight_scale, requires_grad=False)

        weight_global_scale = layer.weight_global_scale.to(torch.float32)
        weight_global_scale = nvfp4_marlin_process_global_scale(
            weight_global_scale, param_dtype
        )
        weight_global_scale = weight_global_scale / scale_factor
        layer.weight_global_scale = torch.nn.Parameter(
            weight_global_scale, requires_grad=False
        )
    else:
        weight_scale = mxfp4_marlin_process_scales(
            weight_scale, input_dtype=input_dtype
        )
        layer.weight_scale = torch.nn.Parameter(weight_scale, requires_grad=False)

    if hasattr(layer, "bias") and layer.bias is not None:
        assert layer.bias.shape == (part_size_n,)
        bias = marlin_permute_bias(layer.bias)
        layer.bias = torch.nn.Parameter(bias, requires_grad=False)

    return