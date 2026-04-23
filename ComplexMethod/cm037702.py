def prepare_fp8_layer_for_marlin(
    layer: torch.nn.Module,
    size_k_first: bool = True,
    input_dtype: torch.dtype | None = None,
) -> None:
    logger.warning_once(
        "Your GPU does not have native support for FP8 computation but "
        "FP8 quantization is being used. Weight-only FP8 compression will "
        "be used leveraging the Marlin kernel. This may degrade "
        "performance for compute-heavy workloads."
    )
    if input_dtype is not None and input_dtype.itemsize == 1:
        raise RuntimeError("Marlin W8A8 is not supported.")

    part_size_n = layer.output_size_per_partition
    part_size_k = layer.input_size_per_partition
    weight_block_size = getattr(layer, "weight_block_size", None)

    if size_k_first:
        assert layer.weight.shape == (part_size_k, part_size_n)
    else:
        assert layer.weight.shape == (part_size_n, part_size_k)

    device = layer.weight.device

    # WORKSPACE
    layer.workspace = marlin_make_workspace_new(device)

    # WEIGHT
    # Repack weights to marlin format
    perm = torch.empty(0, dtype=torch.int, device=device)
    qweight = pack_fp8_to_int32(layer.weight, size_k_first)
    if not size_k_first:
        qweight = qweight.T.contiguous()

    marlin_qweight = ops.gptq_marlin_repack(
        b_q_weight=qweight,
        perm=perm,
        size_k=part_size_k,
        size_n=part_size_n,
        num_bits=8,
    )
    replace_parameter(layer, "weight", marlin_qweight)

    # WEIGHT SCALES
    # Permute scales
    if "weight_scale" in dir(layer):
        scales = layer.weight_scale.to(layer.orig_dtype)
    elif "weight_scale_inv" in dir(layer):
        scales = layer.weight_scale_inv.to(layer.orig_dtype)

    group_size = -1 if weight_block_size is None else weight_block_size[1]

    # marlin kernel only support channel-wise and group-wise quantization
    # we need to convert the scales
    if weight_block_size is None:
        logical_widths = getattr(layer, "logical_widths", [])
        if scales.nelement() == 1:
            # tensor-wise quantization -> channel-wise quantization
            # (1, 1) =>(repeat)=> (1, size_n)
            scales = scales.view(1, 1).repeat_interleave(part_size_n, 1)
        elif scales.nelement() == len(logical_widths):
            # tensor-wise quantization with logical_widths ->
            #    channel-wise quantization
            assert sum(logical_widths) == part_size_n, (
                f"Sum of logical_widths ({sum(logical_widths)}) must be equal "
                f"to part_size_n ({part_size_n})"
            )
            lw_tensor = scales.new_tensor(logical_widths, dtype=torch.int64)
            scales = scales.view(1, -1).repeat_interleave(lw_tensor, dim=1)
        elif scales.nelement() > 1 and scales.nelement() != part_size_n:
            assert part_size_n % scales.nelement() == 0
            s_size = scales.nelement()
            # tensor-wise quantization (for gate-up proj)
            #     -> channel-wise quantization
            # (1, s_size) =>(repeat)=> (1, size_n)
            scales = scales.view(1, s_size)
            scales = scales.repeat_interleave(part_size_n // s_size, 1)
        else:
            # channel-wise quantization
            # (1, size_n)
            scales = scales.view(1, part_size_n)
    else:
        # block-wise quantization -> group-wise quantization
        # (size_k // block_size[1], ceil(size_n / block_size[0]))
        #  =>(repeat)=> (size_k // block_size[1], size_n)
        if not size_k_first:
            scales = scales.T.contiguous()
        block_n = weight_block_size[0]
        scales = scales.repeat_interleave(block_n, 1)
        # size_n may not divisible by block_size[0]
        scales = scales[:, :part_size_n]

    marlin_scales = marlin_permute_scales(
        s=scales, size_k=part_size_k, size_n=part_size_n, group_size=group_size
    )
    if input_dtype != torch.float8_e4m3fn:
        marlin_scales = fp8_fused_exponent_bias_into_scales(marlin_scales)
    if hasattr(layer, "weight_scale"):
        replace_parameter(layer, "weight_scale", marlin_scales)
    elif hasattr(layer, "weight_scale_inv"):
        replace_parameter(layer, "weight_scale_inv", marlin_scales)

    if hasattr(layer, "bias") and layer.bias is not None:
        assert layer.bias.shape == (part_size_n,)
        bias = marlin_permute_bias(layer.bias)
        replace_parameter(layer, "bias", bias)