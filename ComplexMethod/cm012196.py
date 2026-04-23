def _create_new_linear_node(graph, linear_node, binary_node, other):
        assert linear_node.target in [aten.addmm.default, aten.mm.default]
        input_node = (
            linear_node.args[1]
            if linear_node.target is aten.addmm.default
            else linear_node.args[0]
        )
        weight_node = (
            linear_node.args[2]
            if linear_node.target is aten.addmm.default
            else linear_node.args[1]
        )
        bias_node = (
            linear_node.args[0] if linear_node.target is aten.addmm.default else None
        )
        weight_meta_value = weight_node.meta.get("val")
        if binary_node.target in [aten.add.Tensor, aten.sub.Tensor]:
            other_reshape = resize_scalar_or_tensor_to_shape(
                graph,
                other,
                (weight_meta_value.size(1),),
                weight_meta_value,
            )
            new_bias_node = graph.create_node(
                "call_function",
                binary_node.target,
                (0 if bias_node is None else bias_node, other_reshape),
            )
            return graph.create_node(
                "call_function",
                aten.addmm.default,
                (new_bias_node, input_node, weight_node),
            )
        else:
            assert binary_node.target in [aten.mul.Tensor, aten.div.Tensor]
            weight_broadcast_shape = [1, weight_meta_value.size(1)]
            other_reshape1 = resize_scalar_or_tensor_to_shape(
                graph,
                other,
                tuple(weight_broadcast_shape),
                weight_meta_value,
            )
            new_weight_node = graph.create_node(
                "call_function", binary_node.target, (weight_node, other_reshape1)
            )
            new_weight_node.meta.update(weight_node.meta)
            if bias_node is not None:
                other_reshape = resize_scalar_or_tensor_to_shape(
                    graph,
                    other,
                    (weight_meta_value.size(1),),
                    weight_meta_value,
                )
                new_bias_node = graph.create_node(
                    "call_function", binary_node.target, (bias_node, other_reshape)
                )
                new_bias_node.meta.update(bias_node.meta)
                return graph.create_node(
                    "call_function",
                    linear_node.target,
                    (new_bias_node, input_node, new_weight_node),
                )
            else:
                return graph.create_node(
                    "call_function", linear_node.target, (input_node, new_weight_node)
                )