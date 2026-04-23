def qlinear_post_op_fusion(match: Match, *args, **kwargs):
        """
        Match the pattern:
        qlinear - post op
        """
        output_dtype = _get_pattern_output_dtype(match)
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

        # bias
        b = kwargs.get("b")

        # Output QParams
        o_inv_scale = (
            kwargs["o_inv_scale"]
            if (output_dtype in [torch.uint8, torch.int8])
            else 1.0
        )
        o_zero_point = (
            kwargs["o_zp"] if (output_dtype in [torch.uint8, torch.int8]) else 0
        )
        assert (
            kwargs["postop_name"] == "none"
        )  # Expected no post op fused in weight prepack phase

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
                    o_inv_scale,
                    o_zero_point,
                    output_dtype,
                    post_op_attr.unary_op_name,
                    post_op_attr.scalars_attr,
                    post_op_attr.algorithm_attr,
                )
            else:
                other = kwargs["other"] if "other" in kwargs else kwargs["accum"]
                x2_scale = 1.0
                x2_zp = 0
                computation_args = (
                    x,
                    x_scale,
                    x_zp,
                    packed_weight,
                    w_scale,
                    w_zp,
                    other,
                    b,
                    o_inv_scale,
                    o_zero_point,
                    output_dtype,
                    x2_scale,
                    x2_zp,
                    post_op_attr.binary_op_name,
                    post_op_attr.alpha,
                    post_op_attr.unary_op_name,
                    post_op_attr.scalars_attr,
                    post_op_attr.algorithm_attr,
                )
            new_linear_node = match.graph.call_function(
                computation_op, args=computation_args
            )
            out_node.replace_all_uses_with(new_linear_node)
            new_linear_node.meta.update(out_node.meta)
            for node in reversed(match.nodes):
                match.graph.erase_node(node)
        count_key = (
            "qlinear_binary_matcher_count"
            if has_binary_post_op
            else "qlinear_unary_matcher_count"
        )
        nodes_key = (
            "qlinear_binary_matcher_nodes"
            if has_binary_post_op
            else "qlinear_unary_matcher_nodes"
        )
        counters["inductor"][count_key] += 1
        counters["inductor"][nodes_key] += len(match.nodes)