def fuse(self, graph: torch.fx.GraphModule, subset: list[torch.fx.Node]):
        group_inputs = []
        group_shapes = []
        group_weights = []
        group_biases = []
        group_epss = []
        group_nodes = []
        group_inputs_metadata = []
        group_biases_metadata = []
        group_weights_metadata = []
        for node in subset:
            group_nodes.append(node)
            input = get_arg_value(node, 0, "input")
            group_inputs.append(input)
            group_inputs_metadata.append(input.meta["example_value"])
            group_shapes.append(get_arg_value(node, 1, "normalized_shape"))
            weight = get_arg_value(node, 2, "weight")
            group_weights.append(weight)
            if weight is not None and hasattr(weight, "meta"):
                group_weights_metadata.append(weight.meta["example_value"])
            bias = get_arg_value(node, 3, "bias")
            group_biases.append(bias)
            if bias is not None and hasattr(bias, "meta"):
                group_biases_metadata.append(bias.meta["example_value"])
            eps = get_arg_value(node, 4, "eps")
            if eps is None:
                eps = 1e-5
            group_epss.append(eps)
        stack_dim = -1 - len(group_shapes[-1])

        if all(bias is None for bias in group_biases):
            group_biases = None  # type: ignore[assignment]
        if all(weight is None for weight in group_weights):
            group_weights = None  # type: ignore[assignment]
        assert all(eps == group_epss[0] for eps in group_epss), (
            "all epsilon values must be equal"
        )

        with graph.inserting_before(subset[0]):  # type: ignore[operator]
            stack_input = graph.call_function(  # type: ignore[operator]
                torch.stack, args=(group_inputs,), kwargs={"dim": stack_dim}
            )
            update_stack_example_value(stack_input, group_inputs_metadata, stack_dim)
            if group_weights is not None:
                stack_weight = graph.call_function(  # type: ignore[operator]
                    torch.stack, args=(group_weights,), kwargs={"dim": 0}
                )
                update_stack_example_value(stack_weight, group_weights_metadata)
            else:
                stack_weight = None
            if group_biases is not None:
                stack_bias = graph.call_function(  # type: ignore[operator]
                    torch.stack, args=(group_biases,), kwargs={"dim": 0}
                )
                update_stack_example_value(stack_bias, group_biases_metadata)
            else:
                stack_bias = None

            batch_layer_norm = graph.call_function(  # type: ignore[operator]
                torch.nn.functional.layer_norm,
                args=(stack_input, group_shapes[-1]),
                kwargs={"eps": group_epss[-1]},
            )
            batch_layer_norm.meta["example_value"] = stack_input.meta["example_value"]

            if group_weights is not None and group_biases is not None:
                previous_batch_layer_norm_meta = batch_layer_norm.meta["example_value"]
                batch_layer_norm = graph.call_function(  # type: ignore[operator]
                    torch.mul, args=(stack_weight, batch_layer_norm)
                )
                update_pointwise_example_value(
                    batch_layer_norm,
                    # pyrefly: ignore [missing-attribute]
                    stack_weight.meta["example_value"],
                    previous_batch_layer_norm_meta,
                    torch.mul,
                )
                previous_batch_layer_norm_meta = batch_layer_norm.meta["example_value"]
                batch_layer_norm = graph.call_function(  # type: ignore[operator]
                    torch.add, args=(stack_bias, batch_layer_norm)
                )
                update_pointwise_example_value(
                    batch_layer_norm,
                    # pyrefly: ignore [missing-attribute]
                    stack_bias.meta["example_value"],
                    previous_batch_layer_norm_meta,
                    torch.add,
                )
            elif group_weights is not None and group_biases is None:
                previous_batch_layer_norm_meta = batch_layer_norm.meta["example_value"]
                # pyrefly: ignore [not-callable]
                batch_layer_norm = graph.call_function(
                    torch.mul, args=(stack_weight, batch_layer_norm)
                )
                update_pointwise_example_value(
                    batch_layer_norm,
                    # pyrefly: ignore [missing-attribute]
                    stack_weight.meta["example_value"],
                    previous_batch_layer_norm_meta,
                    torch.mul,
                )
            elif group_weights is None and group_biases is not None:
                previous_batch_layer_norm_meta = batch_layer_norm.meta["example_value"]
                # pyrefly: ignore [not-callable]
                batch_layer_norm = graph.call_function(
                    torch.add, args=(stack_bias, batch_layer_norm)
                )
                update_pointwise_example_value(
                    batch_layer_norm,
                    # pyrefly: ignore [missing-attribute]
                    stack_bias.meta["example_value"],
                    previous_batch_layer_norm_meta,
                    torch.add,
                )

            batch_layer_norm_unbind = graph.call_function(  # type: ignore[operator]
                torch.unbind,
                args=(batch_layer_norm,),
                kwargs={"dim": stack_dim},
            )
            update_stack_example_value(
                batch_layer_norm_unbind,
                batch_layer_norm.meta["example_value"],
                op=torch.unbind,
                dim=stack_dim,
            )

        for i, node in enumerate(group_nodes):
            with graph.inserting_after(batch_layer_norm_unbind):  # type: ignore[operator]
                new_node = graph.call_function(  # type: ignore[operator]
                    operator.getitem, args=(batch_layer_norm_unbind, i)
                )
            node.replace_all_uses_with(new_node)
            new_node.meta.update(node.meta)
            graph.erase_node(node)  # type: ignore[operator]
        counters["inductor"]["batch_layernorm"] += 1