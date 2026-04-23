def qconv(match: Match, *args, **kwargs):
        # Activation QParams
        x, x_scale, x_zp = (
            kwargs["x"],
            kwargs["x_scale"],
            kwargs["x_zp"],
        )
        # Weight QParams
        packed_weight, w_scale, w_zp = (
            kwargs["packed_weight"],
            kwargs["w_scale"],
            kwargs["w_zp"],
        )
        # Conv Params
        b, stride, padding, dilation, groups = (
            kwargs["b"],
            kwargs["stride"],
            kwargs["padding"],
            kwargs["dilation"],
            kwargs["groups"],
        )
        output_dtype = _get_pattern_output_dtype(match)
        assert output_dtype in [torch.int8, torch.uint8, torch.float32, torch.bfloat16]
        # Output QParams
        o_inv_scale = (
            kwargs["o_inv_scale"]
            if (output_dtype == torch.uint8 or output_dtype == torch.int8)
            else 1.0
        )
        o_zero_point = (
            kwargs["o_zp"]
            if (output_dtype == torch.uint8 or output_dtype == torch.int8)
            else 0
        )
        assert (
            kwargs["postop_name"] == "none"
        )  # Expected no post op fused in weight prepack phase
        if post_op_attr.unary_op_name == "hardtanh":
            min_value = kwargs.get("min_value")
            max_value = kwargs.get("max_value")
            post_op_attr.scalars_attr = [min_value, max_value]

        out_node = match.output_node()
        with match.graph.inserting_before(out_node):
            if not has_binary_post_op:
                computation_args: tuple[Any, ...] = (
                    x,
                    x_scale,
                    x_zp,
                    packed_weight,
                    w_scale,
                    w_zp,
                    b,
                    stride,
                    padding,
                    dilation,
                    groups,
                    o_inv_scale,
                    o_zero_point,
                    output_dtype,
                    post_op_attr.unary_op_name,
                    post_op_attr.scalars_attr,
                    post_op_attr.algorithm_attr,
                )
            else:
                accum = (
                    kwargs["accum"]
                    if output_dtype in [torch.uint8, torch.int8]
                    else kwargs["accum_after_dequant"]
                )
                accum_scale = (
                    kwargs["accum_scale"]
                    if output_dtype in [torch.uint8, torch.int8]
                    else 1.0
                )
                accum_zp = (
                    kwargs["accum_zp"]
                    if output_dtype in [torch.uint8, torch.int8]
                    else 0
                )
                computation_args = (
                    x,
                    x_scale,
                    x_zp,
                    packed_weight,
                    w_scale,
                    w_zp,
                    accum,
                    b,
                    stride,
                    padding,
                    dilation,
                    groups,
                    o_inv_scale,
                    o_zero_point,
                    output_dtype,
                    accum_scale,
                    accum_zp,
                    post_op_attr.binary_op_name,
                    post_op_attr.alpha,
                    post_op_attr.unary_op_name,
                    post_op_attr.scalars_attr,
                    post_op_attr.algorithm_attr,
                )
            new_conv_node = match.graph.call_function(
                computation_op, args=computation_args
            )
            out_node.replace_all_uses_with(new_conv_node)
            new_conv_node.meta.update(out_node.meta)
            for node in reversed(match.nodes):
                match.graph.erase_node(node)
        count_key = (
            "qconv2d_binary_matcher_count"
            if has_binary_post_op
            else "qconv_unary_matcher_count"
        )
        nodes_key = (
            "qconv2d_binary_matcher_nodes"
            if has_binary_post_op
            else "qconv_unary_matcher_nodes"
        )
        counters["inductor"][count_key] += 1
        counters["inductor"][nodes_key] += len(match.nodes)