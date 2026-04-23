def _register_qlinear_binary_fusion():
    r"""
    Supported linear-binary(-unary) patterns

        linear(X)   extra input
               \   /
                Add
                 |
            Optional(relu)
                 |
                 Y

    1. int8-mixed-fp32
    +---+---------------+-----------+------------------------------+---------+
    | # | Add type      | Quant out | Pattern                      | Post op |
    +---+---------------+-----------+------------------------------+---------+
    | 1 | In-/out-place | Yes       | linear + fp32 -> (relu) -> q | add     |
    +---+---------------+-----------+------------------------------+---------+
    | 2 | In-/out-place | No        | linear + fp32 -> (relu)      | sum     |
    +---+---------------+-----------+------------------------------+---------+

    2. int8-mixed-bf16
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | # | X2 dtype | Add type      | Quant out | Pattern                                 | Post op |
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | 1 | BF16     | In-/out-place | Yes       | linear + bf16 -> (relu) -> q            | add     |
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | 2 | BF16     | In-/out-place | No        | linear + bf16 -> (relu)                 | sum     |
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | 3 | FP32     | Out-place     | Yes       | linear + fp32 -> (relu) -> q            | add     |
    |   |          | In-place right|           |                                         |         |
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | 4 | FP32     | Out-place     | No        | linear + fp32 -> (relu)                 | sum     |
    |   |          | In-place right|           |                                         |         |
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | 5 | FP32     | In-place left | Yes       | linear + fp32 -> to_bf16 -> (relu) -> q | add     |
    +---+----------+---------------+-----------+-----------------------------------------+---------+
    | 6 | FP32     | In-place left | No        | linear + fp32 -> to_bf16 -> (relu)      | add     |
    +---+----------+---------------+-----------+-----------------------------------------+---------+

    Note
    (1) The positions of linear and the extra input can be swapped.
    (2) we don't insert q-dq before the extra input of linear-add by recipe. But if q-dq is found at the
    extra input, we don't match that pattern because we cannot match all these patterns in 3 passes.
    """
    for x_scale_zp_are_tensors in (False, True):
        qlinear_binary_op = (
            torch.ops.onednn.qlinear_pointwise.binary_tensor
            if x_scale_zp_are_tensors
            else torch.ops.onednn.qlinear_pointwise.binary
        )
        unary_postop_list = ["none", "relu"]
        unary_postop_dict = {
            "none": None,
            "relu": aten.relu.default,
        }
        convert_dtype_after_binary_list = [False, True]

        # Priority 1 to match: QLinear Binary or Binary-Unary pattern with int8 output
        # Covers case (1) of int8-mixed-fp32 and case (1)(3)(5) of int8-mixed-bf16,
        # totally 3 patterns (2 are identical)
        swap_binary_inputs_list = [False, True]
        int8_mixed_bf16_list = [False, True]
        combinations = itertools.product(
            unary_postop_list,
            int8_mixed_bf16_list,
            swap_binary_inputs_list,
            convert_dtype_after_binary_list,
        )
        qlinear_binary_replace_patterns = {}
        for unary_op, int8_mixed_bf16, swap_inputs, cvt_dtype_binary in combinations:
            if not int8_mixed_bf16 and cvt_dtype_binary:
                # No convert node after binary node if dtypes are all fp32
                continue
            qlinear_binary_replace_patterns.update(
                {
                    PostOpAttr(
                        "add", 1.0, unary_op, [], ""
                    ): generate_pattern_with_output_quant(
                        generate_pattern_with_unary(
                            generate_pattern_with_binary(
                                aten.add.Tensor,
                                get_qlinear_pt2e_pattern(x_scale_zp_are_tensors),
                                KeywordArg("other"),
                                # If fp32 extra input is inplace added to bf16 linear output,
                                # a to_bf16 node is inserted after binary
                                dtype_convert=cvt_dtype_binary,
                                swap_inputs=swap_inputs,
                            ),
                            unary_postop_dict[unary_op],
                        ),
                    )
                }
            )
        for binary_unary_attr, patterns in qlinear_binary_replace_patterns.items():
            _register_qlinear_post_op_fusion_pass(
                patterns,
                3,  # pass_number
                qlinear_binary_op,  # computation_op
                binary_unary_attr,
            )

        # Priority 2.1 to match: QLinear Binary-Unary pattern with fp32/bfloat16 output
        # Covers case (2) of int8-mixed-fp32 and case (2)(4) of int8-mixed-bf16,
        # totally 2 patterns (2 are identical)
        binary_replace_float_out_patterns = {}
        for swap_binary_inputs in swap_binary_inputs_list:
            binary_replace_float_out_patterns.update(
                {
                    PostOpAttr("sum", 1.0, "relu", [], ""): generate_pattern_with_unary(
                        generate_pattern_with_binary(
                            aten.add.Tensor,
                            get_qlinear_pt2e_pattern(x_scale_zp_are_tensors),
                            KeywordArg("accum"),
                            dtype_convert=False,
                            swap_inputs=swap_binary_inputs,
                        ),
                        aten.relu.default,
                    ),
                }
            )
        for (
            binary_unary_attr,
            patterns,
        ) in binary_replace_float_out_patterns.items():
            _register_qlinear_post_op_fusion_pass(
                patterns,
                4,  # pass_number
                qlinear_binary_op,  # computation_op
                binary_unary_attr,
            )
        # Priority 2.2 to match: QLinear Binary-Unary pattern with fp32/bfloat16 output
        # Covers case (6) of int8-mixed-bf16
        binary_replace_float_out_patterns = {}
        for swap_binary_inputs in swap_binary_inputs_list:
            binary_replace_float_out_patterns.update(
                {
                    PostOpAttr("add", 1.0, "relu", [], ""): generate_pattern_with_unary(
                        generate_pattern_with_binary(
                            aten.add.Tensor,
                            get_qlinear_pt2e_pattern(x_scale_zp_are_tensors),
                            KeywordArg("other"),
                            dtype_convert=True,
                            swap_inputs=swap_binary_inputs,
                        ),
                        aten.relu.default,
                    ),
                }
            )
        for (
            binary_unary_attr,
            patterns,
        ) in binary_replace_float_out_patterns.items():
            _register_qlinear_post_op_fusion_pass(
                patterns,
                4,  # pass_number
                qlinear_binary_op,  # computation_op
                binary_unary_attr,
            )

        # Priority 3.1: QLinear Binary pattern with fp32/bfloat16 output
        # Covers case (2) of int8-mixed-fp32 and case (2)(4) of int8-mixed-bf16,
        # totally 2 patterns (2 are identical)
        binary_replace_float_out_patterns = {}
        for swap_binary_inputs in swap_binary_inputs_list:
            binary_replace_float_out_patterns.update(
                {
                    PostOpAttr(
                        "sum", 1.0, "none", [], ""
                    ): generate_pattern_with_binary(
                        aten.add.Tensor,
                        get_qlinear_pt2e_pattern(x_scale_zp_are_tensors),
                        KeywordArg("accum"),
                        dtype_convert=False,
                        swap_inputs=swap_binary_inputs,
                    ),
                }
            )
        for (
            binary_unary_attr,
            patterns,
        ) in binary_replace_float_out_patterns.items():
            _register_qlinear_post_op_fusion_pass(
                patterns,
                5,  # pass_number
                qlinear_binary_op,  # computation_op
                binary_unary_attr,
            )
        # Priority 3.2: QLinear Binary pattern with fp32/bfloat16 output
        # Covers (6) of int8-mixed-bf16
        binary_replace_float_out_patterns = {}
        for swap_binary_inputs in swap_binary_inputs_list:
            binary_replace_float_out_patterns.update(
                {
                    PostOpAttr(
                        "add", 1.0, "none", [], ""
                    ): generate_pattern_with_binary(
                        aten.add.Tensor,
                        get_qlinear_pt2e_pattern(x_scale_zp_are_tensors),
                        KeywordArg("other"),
                        dtype_convert=True,
                        swap_inputs=swap_binary_inputs,
                    ),
                }
            )
        for (
            binary_unary_attr,
            patterns,
        ) in binary_replace_float_out_patterns.items():
            _register_qlinear_post_op_fusion_pass(
                patterns,
                5,  # pass_number
                qlinear_binary_op,  # computation_op
                binary_unary_attr,
            )