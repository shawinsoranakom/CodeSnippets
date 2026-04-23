def _register_qconv_unary_fusion():
    from .mkldnn_fusion import _hardswish_fusion, _hardtanh_fusion, _silu_fusion

    for original_pattern_output_dtype in [torch.float32, torch.bfloat16]:
        # Priority 1 to match: QConv2d Unary pattern with int8 output
        # If a pattern1 is a sub-set of pattern2, we should try to match pattern2 firstly.
        # For example: pattern1 is qconv_fp32 -> relu, pattern2 is qconv_fp32 -> relu -> quant
        is_bf16 = original_pattern_output_dtype == torch.bfloat16
        conv_unary_replace_patterns = {
            PostOpAttr(
                "none", None, "none", [], ""
            ): generate_pattern_with_output_quant(
                get_qconv_pt2e_pattern(users=1),
            ),
            PostOpAttr(
                "none", None, "relu", [], ""
            ): generate_pattern_with_output_quant(
                generate_pattern_with_unary(
                    get_qconv_pt2e_pattern(users=1), aten.relu.default
                ),
            ),
            PostOpAttr(
                "none", None, "hardtanh", [], ""
            ): generate_pattern_with_output_quant(
                _unary_fusion_pattern(
                    _hardtanh_fusion,
                    get_qconv_pt2e_pattern(users=1),
                    1,
                    is_bf16,
                ),
                with_dtype_convert=is_bf16,
            ),
            PostOpAttr(
                "none", None, "hardswish", [], ""
            ): generate_pattern_with_output_quant(
                _unary_fusion_pattern(
                    _hardswish_fusion,
                    get_qconv_pt2e_pattern(users=1 if is_bf16 else 2),
                    2,
                    is_bf16,
                ),
                with_dtype_convert=is_bf16,
            ),
            PostOpAttr(
                "none", None, "swish", [], ""
            ): generate_pattern_with_output_quant(
                _unary_fusion_pattern(
                    _silu_fusion,
                    get_qconv_pt2e_pattern(users=1 if is_bf16 else 2),
                    2,
                    is_bf16,
                ),
                with_dtype_convert=is_bf16,
            ),
        }

        for unary_attr, patterns in conv_unary_replace_patterns.items():
            # Register qconv2d pattern for ExternKernel Lowering
            _register_qconv_post_op_fusion_pass(
                patterns,
                3,  # pass_number
                torch.ops.onednn.qconv_pointwise.default,  # computation_op
                unary_attr,  # unary_attr
            )

        # Priority 2 to match: QConv2d Unary pattern with fp32/bfloat16 output
        conv_unary_replace_float_out_patterns = {
            PostOpAttr("none", None, "relu", [], ""): generate_pattern_with_unary(
                get_qconv_pt2e_pattern(users=1), aten.relu.default
            ),
            PostOpAttr(
                "none", None, "hardtanh", [], ""
            ): _may_generate_pattern_with_dtype_convert(
                _unary_fusion_pattern(
                    _hardtanh_fusion,
                    get_qconv_pt2e_pattern(users=1),
                    1,
                    is_bf16,
                ),
                Arg(),
                is_bf16,
            ),
            PostOpAttr(
                "none", None, "hardswish", [], ""
            ): _may_generate_pattern_with_dtype_convert(
                _unary_fusion_pattern(
                    _hardswish_fusion,
                    get_qconv_pt2e_pattern(users=1 if is_bf16 else 2),
                    2,
                    is_bf16,
                ),
                Arg(),
                is_bf16,
            ),
            PostOpAttr(
                "none", None, "swish", [], ""
            ): _may_generate_pattern_with_dtype_convert(
                _unary_fusion_pattern(
                    _silu_fusion,
                    get_qconv_pt2e_pattern(users=1 if is_bf16 else 2),
                    2,
                    is_bf16,
                ),
                Arg(),
                is_bf16,
            ),
        }

        for unary_attr, patterns in conv_unary_replace_float_out_patterns.items():
            # Register qconv2d pattern for ExternKernel Lowering
            _register_qconv_post_op_fusion_pass(
                patterns,
                4,  # pass_number
                torch.ops.onednn.qconv_pointwise.default,  # computation_op
                unary_attr,  # unary_attr
            )