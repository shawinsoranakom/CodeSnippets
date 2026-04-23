def _register_qconv_binary_fusion():
    for int8_mixed_bf16_with_inplace_add in [False, True]:
        # Priority 1 to match: QConv2d Binary or Binary-Unary pattern with int8 output
        swap_binary_inputs_list = [False, True]
        binary_replace_patterns = {}
        for swap_inputs in swap_binary_inputs_list:
            binary_replace_patterns.update(
                {
                    PostOpAttr(
                        "sum", 1.0, "none", [], ""
                    ): generate_pattern_with_output_quant(
                        generate_pattern_with_binary(
                            aten.add.Tensor,
                            get_qconv_pt2e_pattern(users=1),
                            dequantize_accum_pattern,
                            int8_mixed_bf16_with_inplace_add,
                            swap_inputs=swap_inputs,
                        ),
                    ),
                    PostOpAttr(
                        "sum", 1.0, "relu", [], ""
                    ): generate_pattern_with_output_quant(
                        generate_pattern_with_unary(
                            generate_pattern_with_binary(
                                aten.add.Tensor,
                                get_qconv_pt2e_pattern(users=1),
                                dequantize_accum_pattern,
                                int8_mixed_bf16_with_inplace_add,
                                swap_inputs=swap_inputs,
                            ),
                            aten.relu.default,
                        ),
                    ),
                }
            )

        for binary_unary_attr, patterns in binary_replace_patterns.items():
            _register_qconv_post_op_fusion_pass(
                patterns,
                3,  # pass_number
                torch.ops.onednn.qconv2d_pointwise.binary,  # computation_op
                binary_unary_attr,  # binary_unary_attr
            )

        # Priority 2 to match: QConv2d Binary-Unary pattern with fp32/bfloat16 output
        binary_replace_float_out_patterns = {}
        for swap_inputs in swap_binary_inputs_list:
            binary_replace_float_out_patterns.update(
                {
                    PostOpAttr("sum", 1.0, "relu", [], ""): generate_pattern_with_unary(
                        generate_pattern_with_binary(
                            aten.add.Tensor,
                            get_qconv_pt2e_pattern(users=1),
                            KeywordArg("accum_after_dequant"),
                            int8_mixed_bf16_with_inplace_add,
                            swap_inputs=swap_inputs,
                        ),
                        aten.relu.default,
                    )
                }
            )

        for (
            binary_unary_attr,
            patterns,
        ) in binary_replace_float_out_patterns.items():
            if int8_mixed_bf16_with_inplace_add:
                _register_qconv_post_op_fusion_pass(
                    patterns,
                    3,  # pass_number
                    torch.ops.onednn.qconv2d_pointwise.binary,  # computation_op
                    binary_unary_attr,  # binary_unary_attr
                )
            else:
                _register_qconv_post_op_fusion_pass(
                    patterns,
                    4,  # pass_number
                    torch.ops.onednn.qconv2d_pointwise.binary,  # computation_op
                    binary_unary_attr,  # binary_unary_attr
                )

        # Priority 3: QConv2d Binary pattern with fp32/bfloat16 output
        binary_replace_float_out_patterns = {}
        for swap_inputs in swap_binary_inputs_list:
            binary_replace_float_out_patterns.update(
                {
                    PostOpAttr(
                        "sum", 1.0, "none", [], ""
                    ): generate_pattern_with_binary(
                        aten.add.Tensor,
                        get_qconv_pt2e_pattern(users=1),
                        KeywordArg("accum_after_dequant"),
                        int8_mixed_bf16_with_inplace_add,
                        swap_inputs=swap_inputs,
                    ),
                }
            )

        for (
            binary_unary_attr,
            patterns,
        ) in binary_replace_float_out_patterns.items():
            _register_qconv_post_op_fusion_pass(
                patterns,
                4 if int8_mixed_bf16_with_inplace_add else 5,  # pass_number
                torch.ops.onednn.qconv2d_pointwise.binary,  # computation_op
                binary_unary_attr,  # binary_unary_attr
            )