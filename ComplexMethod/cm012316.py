def _register_qlinear_unary_fusion():
    from .mkldnn_fusion import (
        _gelu_fusion_1 as _gelu_fusion_erf,
        _gelu_fusion_2 as _gelu_fusion_tanh,
    )

    for original_pattern_output_dtype in [torch.float32, torch.bfloat16]:
        is_bf16 = original_pattern_output_dtype == torch.bfloat16
        for x_scale_zp_are_tensors in (False, True):
            qlinear_pattern = get_qlinear_pt2e_pattern(x_scale_zp_are_tensors)
            computation_op = (
                torch.ops.onednn.qlinear_pointwise.tensor
                if x_scale_zp_are_tensors
                else torch.ops.onednn.qlinear_pointwise.default
            )
            # Priority 1 to match: QLinear Unary pattern with int8 output
            linear_unary_replace_patterns = {
                PostOpAttr(
                    "none", None, "none", [], ""
                ): generate_pattern_with_output_quant(
                    qlinear_pattern,
                ),
                PostOpAttr(
                    "none", None, "relu", [], ""
                ): generate_pattern_with_output_quant(
                    generate_pattern_with_unary(qlinear_pattern, aten.relu.default),
                ),
                PostOpAttr(
                    "none", None, "gelu", [], "none"
                ): generate_pattern_with_output_quant(
                    _unary_fusion_pattern(
                        _gelu_fusion_erf,
                        get_qlinear_pt2e_pattern(
                            x_scale_zp_are_tensors, 1 if is_bf16 else 2
                        ),
                        2,
                        is_bf16,
                    ),
                    with_dtype_convert=is_bf16,
                ),
                PostOpAttr(
                    "none", None, "gelu", [], "tanh"
                ): generate_pattern_with_output_quant(
                    _unary_fusion_pattern(
                        _gelu_fusion_tanh,
                        get_qlinear_pt2e_pattern(
                            x_scale_zp_are_tensors, 1 if is_bf16 else 4
                        ),
                        4,
                        is_bf16,
                    ),
                    with_dtype_convert=is_bf16,
                ),
            }

            for unary_attr, patterns in linear_unary_replace_patterns.items():
                _register_qlinear_post_op_fusion_pass(
                    patterns,
                    3,  # pass_number
                    computation_op,
                    unary_attr,  # unary_attr
                )

            # Priority 2 to match: QLinear Unary pattern with FP32/BF16 output
            linear_unary_replace_float_out_patterns = {
                PostOpAttr("none", None, "relu", [], ""): generate_pattern_with_unary(
                    qlinear_pattern, aten.relu.default
                ),
                PostOpAttr(
                    "none", None, "gelu", [], "none"
                ): _may_generate_pattern_with_dtype_convert(
                    _unary_fusion_pattern(
                        _gelu_fusion_erf,
                        get_qlinear_pt2e_pattern(
                            x_scale_zp_are_tensors, 1 if is_bf16 else 2
                        ),
                        2,
                        is_bf16,
                    ),
                    Arg(),
                    is_bf16,
                ),
                PostOpAttr(
                    "none", None, "gelu", [], "tanh"
                ): _may_generate_pattern_with_dtype_convert(
                    _unary_fusion_pattern(
                        _gelu_fusion_tanh,
                        get_qlinear_pt2e_pattern(
                            x_scale_zp_are_tensors, 1 if is_bf16 else 4
                        ),
                        4,
                        is_bf16,
                    ),
                    Arg(),
                    is_bf16,
                ),
            }

            for unary_attr, patterns in linear_unary_replace_float_out_patterns.items():
                _register_qlinear_post_op_fusion_pass(
                    patterns,
                    4,  # pass_number
                    computation_op,
                    unary_attr,  # unary_attr
                )