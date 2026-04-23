def linear_dynamic_fp16_weight_prepack(match: Match, *args, **kwargs):
        """
        Match the pattern:
        fp32 activation
          |
        mm/addmm <- t <- to_fp32 <- to_fp16 <- weight
          |
        (reshape) <- (relu)

        OR

        fp32 activation
          |
        expand
          |
         bmm <- expand <- t <- to_fp32 <- to_fp16 <- weight
          |
        (add) <- (relu)

        Insert weight prepack node and change the pattern to:
        fp32 activation
          |
        onednn.linear_dynamic_fp16 <- onednn.linear_prepack_fp16 <- weight
        (or onednn.linear_relu_dynamic_fp16)
        """
        # find params
        x = kwargs["x"]
        w = kwargs["w"]
        bias = kwargs.get("b")

        # find linear node
        nodes_to_find = [aten.addmm.default, aten.mm.default, aten.bmm.default]
        linear_nodes = []
        for node in nodes_to_find:
            linear_nodes.extend(filter_nodes(match.nodes, node))
        assert len(linear_nodes) == 1
        linear_node = linear_nodes[0]
        assert isinstance(linear_node, torch.fx.node.Node)
        input_index = 1 if linear_node.target is aten.addmm.default else 0
        weight_index = input_index + 1

        # find relu node
        relu_node = None
        if relu_fused:
            relu_node = match.output_node()
            assert isinstance(relu_node, torch.fx.node.Node)

        # find reshape node, expand node and add node
        (
            act_reshape_node,
            output_reshape_node,
            expand_x_node,
            expand_w_node,
            add_bias_node,
        ) = (None, None, None, None, None)
        t_node = None
        if input_dim_exceeds_two:
            if input_contiguous:
                act_reshape_node = linear_node.args[input_index]
                t_node = linear_node.args[weight_index]
                output_reshape_node = next(iter(linear_node.users))
                assert output_reshape_node.target is aten.reshape.default
            else:
                expand_x_node = linear_node.args[input_index]
                expand_w_node = linear_node.args[weight_index]
                assert isinstance(expand_w_node, torch.fx.node.Node)
                t_node = expand_w_node.args[0]
                if bias:
                    add_bias_node = next(iter(linear_node.users))
                    assert add_bias_node.target is aten.add.Tensor
        else:
            t_node = linear_node.args[weight_index]
        assert isinstance(t_node, torch.fx.node.Node)

        w_to_fp32_node = t_node.args[0]
        assert (
            isinstance(w_to_fp32_node, torch.fx.node.Node)
            and w_to_fp32_node.target
            is quantized_decomposed.convert_element_type.no_fuse
        )
        w_to_fp16_node = w_to_fp32_node.args[0]
        assert (
            isinstance(w_to_fp16_node, torch.fx.node.Node)
            and w_to_fp16_node.target
            is quantized_decomposed.convert_element_type.no_fuse
        )

        x_shape = x.meta.get("tensor_meta").shape
        if has_free_symbols(x_shape):
            # For dynamic shape case, we can't get activation shape ahead of runtime.
            x_shape = None
        graph = match.graph
        with graph.inserting_before(linear_node):
            # Insert weight prepack node and the qlinear node
            packed_weight_inputs = (
                w,
                x_shape,
            )
            packed_weight_op = torch.ops.onednn.linear_prepack_fp16
            prepack_weight_node = graph.call_function(
                packed_weight_op, args=packed_weight_inputs
            )

            # create new linear node and insert on graph
            new_args: tuple[Any, ...] = (
                x,
                prepack_weight_node,
                bias,
            )
            linear_op = (
                torch.ops.onednn.linear_relu_dynamic_fp16.default
                if relu_fused
                else torch.ops.onednn.linear_dynamic_fp16.default
            )
            new_linear_node = graph.call_function(linear_op, args=new_args)
            out_node = match.output_node()
            out_node.replace_all_uses_with(new_linear_node)

            # Erase the original nodes in the reverse order
            new_linear_node.meta.update(out_node.meta)
            if relu_node is not None:
                graph.erase_node(relu_node)
            if output_reshape_node is not None:
                graph.erase_node(output_reshape_node)
            if add_bias_node is not None:
                graph.erase_node(add_bias_node)
            graph.erase_node(linear_node)
            if act_reshape_node is not None:
                assert isinstance(act_reshape_node, torch.fx.node.Node)
                graph.erase_node(act_reshape_node)
            if expand_x_node is not None:
                assert isinstance(expand_x_node, torch.fx.node.Node)
                graph.erase_node(expand_x_node)
            if expand_w_node is not None:
                assert isinstance(expand_w_node, torch.fx.node.Node)
                graph.erase_node(expand_w_node)
            graph.erase_node(t_node)
            graph.erase_node(w_to_fp32_node)
            graph.erase_node(w_to_fp16_node)

            counters["inductor"]["qlinear_weight_prepack_matcher_count"] += 1
            counters["inductor"]["qlinear_weight_prepack_matcher_nodes"] += len(
                match.nodes
            )