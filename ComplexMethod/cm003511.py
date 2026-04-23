def _fuse_experts_for_layer(
    grouped: dict[tuple, dict[int, torch.Tensor]],
    layer_idx: int,
    n_experts: int,
    base: str,
    output_fp8: bool,
) -> dict[str, torch.Tensor]:
    r"""Fuse per-expert weights for a single layer"""
    merge_op = MergeModulelist(dim=0)

    w1 = grouped[(layer_idx, "w1", "weight")]
    w2 = grouped[(layer_idx, "w2", "weight")]
    w3 = grouped[(layer_idx, "w3", "weight")]

    w1_scales = grouped.get((layer_idx, "w1", "qscale_weight"))
    w2_scales = grouped.get((layer_idx, "w2", "qscale_weight"))
    w3_scales = grouped.get((layer_idx, "w3", "qscale_weight"))

    result: dict[str, torch.Tensor] = {}

    if output_fp8:
        fp8_fuse_op = FP8RescaleMergeAndConcatenate()
        gate_up_result = fp8_fuse_op.convert(
            input_dict={
                "w1.weight": [w1[e] for e in range(n_experts)],
                "w3.weight": [w3[e] for e in range(n_experts)],
                "w1.qscale_weight": [w1_scales[e] for e in range(n_experts)],
                "w3.qscale_weight": [w3_scales[e] for e in range(n_experts)],
            },
            source_patterns=["w1.weight", "w3.weight", "w1.qscale_weight", "w3.qscale_weight"],
            target_patterns=["gate_up_proj", "gate_up_proj_scale_inv"],
        )
        result[f"{base}.gate_up_proj"] = gate_up_result["gate_up_proj"]
        result[f"{base}.gate_up_proj_scale_inv"] = gate_up_result["gate_up_proj_scale_inv"]

        down_result = merge_op.convert(
            input_dict={"w2": [w2[e] for e in range(n_experts)]},
            source_patterns=["w2"],
            target_patterns=["down_proj"],
        )
        result[f"{base}.down_proj"] = down_result["down_proj"]
        down_proj_scale_inv = torch.stack([w2_scales[e] for e in range(n_experts)])
        while down_proj_scale_inv.ndim < 3:
            down_proj_scale_inv = down_proj_scale_inv.unsqueeze(-1)
        result[f"{base}.down_proj_scale_inv"] = down_proj_scale_inv

        w1_act = grouped.get((layer_idx, "w1", "qscale_act"))
        if w1_act is not None:
            w2_act = grouped[(layer_idx, "w2", "qscale_act")]
            w3_act = grouped[(layer_idx, "w3", "qscale_act")]
            result[f"{base}.gate_up_proj_activation_scale"] = torch.stack(
                [torch.max(w1_act[e], w3_act[e]) for e in range(n_experts)]
            )
            result[f"{base}.down_proj_activation_scale"] = torch.stack([w2_act[e] for e in range(n_experts)])
    else:
        concat_op = Concatenate(dim=1)

        w1_list = [_descale_fp8_to_bf16(w1[e], w1_scales[e]) if w1_scales else w1[e] for e in range(n_experts)]
        w3_list = [_descale_fp8_to_bf16(w3[e], w3_scales[e]) if w3_scales else w3[e] for e in range(n_experts)]
        w2_list = [_descale_fp8_to_bf16(w2[e], w2_scales[e]) if w2_scales else w2[e] for e in range(n_experts)]

        step1 = merge_op.convert(
            input_dict={"w1": w1_list, "w3": w3_list},
            source_patterns=["w1", "w3"],
            target_patterns=["gate_up_proj"],
        )
        gate_up = concat_op.convert(step1, source_patterns=["w1", "w3"], target_patterns=["gate_up_proj"])
        result[f"{base}.gate_up_proj"] = gate_up["gate_up_proj"]

        down = merge_op.convert(
            input_dict={"w2": w2_list},
            source_patterns=["w2"],
            target_patterns=["down_proj"],
        )
        result[f"{base}.down_proj"] = down["down_proj"]

    return result