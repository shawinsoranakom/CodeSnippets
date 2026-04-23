def qlinear_weight_prepack(match: Match, *args, **kwargs):
        """
        Match the pattern:
        int8 activation
          |
        dequant_per_tensor
          |
        mm/addmm <- t <- dequant_per_channel <- int8_weight

        Insert weight prepack node and change the pattern to:
        int8 activation
          |
        onednn.qlinear_pointwise <- onednn.qlinear_prepack <- int8_weight
        """
        assert dtype in [torch.float32, torch.bfloat16]
        (
            linear_node,
            output_reshape_node,
        ) = _get_linear_node(match, input_dim_exceeds_two, input_contiguous)
        input_index = 1 if linear_node.target is aten.addmm.default else 0
        weight_index = input_index + 1

        (
            dequant_node,
            act_reshape_node,
            activation_to_bf16_node,
            act_expand_node,
        ) = _get_linear_dq_node(
            linear_node,
            input_index,
            input_dim_exceeds_two,
            input_contiguous,
            with_dtype_convert,
        )

        if input_dim_exceeds_two and not input_contiguous:
            wgt_expand_node = linear_node.args[weight_index]
            assert wgt_expand_node.target is aten.expand.default
            t_node = wgt_expand_node.args[0]
        else:
            t_node = linear_node.args[weight_index]

        if dtype == torch.float32:
            dequant_per_channel = t_node.args[0]
        else:
            weight_to_bf16_node = t_node.args[0]
            dequant_per_channel = weight_to_bf16_node.args[0]
        assert (
            dequant_per_channel.target
            is quantized_decomposed.dequantize_per_channel.default
        )

        # Activation QParams
        qx, x_zp, x_scale = (
            kwargs["x"],
            kwargs["x_zp"],
            kwargs["x_scale"],
        )

        # Weight QParams
        qw, w_scale, w_zp = (
            kwargs["q_weight"],
            kwargs["w_scale"],
            kwargs["w_zp"],
        )

        # Params
        bias = kwargs.get("b")

        x_shape = qx.meta.get("tensor_meta").shape
        if has_free_symbols(x_shape):
            # For dynamic shape case, we can't get activation shape ahead of runtime.
            x_shape = None
        graph = match.graph
        with graph.inserting_before(linear_node):
            # Insert weight prepack node and the qlinear node
            packed_weight_inputs = (
                qw,
                x_shape,
            )
            packed_weight_op = torch.ops.onednn.qlinear_prepack
            prepack_weight_node = graph.call_function(
                packed_weight_op, args=packed_weight_inputs
            )

            new_args: tuple[Any, ...] = (
                qx,
                x_scale,
                x_zp,
                prepack_weight_node,
                w_scale,
                w_zp,
                bias,
                1.0,  # output_scale
                0,  # output_zero_point
                dtype,  # output_dtype
                "none",  # post op name
                [],  # post op args
                "",  # post op algorithm
            )
            Node = torch.fx.node.Node
            if isinstance(x_scale, Node) and isinstance(x_zp, Node):
                new_linear_node = graph.call_function(
                    torch.ops.onednn.qlinear_pointwise.tensor, args=new_args
                )
            else:
                new_linear_node = graph.call_function(
                    torch.ops.onednn.qlinear_pointwise.default, args=new_args
                )
            if input_dim_exceeds_two:
                if input_contiguous:
                    output_reshape_node.replace_all_uses_with(new_linear_node)
                    new_linear_node.meta.update(output_reshape_node.meta)
                else:
                    if bias:
                        output_add_node_for_bias = match.output_node()
                        assert output_add_node_for_bias.target is aten.add.Tensor
                        output_add_node_for_bias.replace_all_uses_with(new_linear_node)
                        new_linear_node.meta.update(output_add_node_for_bias.meta)
                    else:
                        linear_node.replace_all_uses_with(new_linear_node)
                        new_linear_node.meta.update(linear_node.meta)
            else:
                linear_node.replace_all_uses_with(new_linear_node)
                new_linear_node.meta.update(linear_node.meta)

            # Erase the original linear node
            if input_dim_exceeds_two:
                if input_contiguous:
                    graph.erase_node(output_reshape_node)
                elif not input_contiguous and bias:
                    graph.erase_node(output_add_node_for_bias)  # type: ignore[possibly-undefined]
            graph.erase_node(linear_node)
            if input_dim_exceeds_two:
                if input_contiguous:
                    graph.erase_node(act_reshape_node)
                else:
                    graph.erase_node(act_expand_node)
                    graph.erase_node(wgt_expand_node)  # type: ignore[possibly-undefined]
            if with_dtype_convert:
                graph.erase_node(activation_to_bf16_node)
            # Erase the dequant pattern
            graph.erase_node(dequant_node)
            # Erase the dequant per channel pattern
            graph.erase_node(t_node)
            if dtype == torch.bfloat16:
                graph.erase_node(weight_to_bf16_node)  # type: ignore[possibly-undefined]
            graph.erase_node(dequant_per_channel)

            counters["inductor"]["qlinear_weight_prepack_matcher_count"] += 1
            counters["inductor"]["qlinear_weight_prepack_matcher_nodes"] += len(
                match.nodes
            )