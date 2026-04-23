def fuse(self, graph: torch.fx.GraphModule, subset: list[torch.fx.Node]):
        batch_nodes = []
        batch_inputs = []
        batch_weights = []
        batch_biases = []
        batch_inputs_metadata = []
        batch_weights_metadata = []
        batch_biases_metadata = []
        for node in subset:
            batch_nodes.append(node)
            input = get_arg_value(node, 0, "input")
            batch_inputs.append(input)
            batch_inputs_metadata.append(input.meta["example_value"])
            weight = get_arg_value(node, 1, "weight")
            batch_weights.append(weight)
            batch_weights_metadata.append(weight.meta["example_value"])
            bias = get_arg_value(node, 2, "bias")
            batch_biases.append(bias)
            if bias is not None and hasattr(bias, "meta"):
                batch_biases_metadata.append(bias.meta["example_value"])

        with graph.inserting_before(subset[0]):  # type: ignore[operator]
            stack_inputs = graph.call_function(  # type: ignore[operator]
                torch.stack, args=(batch_inputs,), kwargs={"dim": 0}
            )
            update_stack_example_value(stack_inputs, batch_inputs_metadata)
            stack_weights = graph.call_function(  # type: ignore[operator]
                torch.stack, args=(batch_weights,), kwargs={"dim": 0}
            )
            update_stack_example_value(stack_weights, batch_weights_metadata)
            transpose_weight = graph.call_function(  # type: ignore[operator]
                torch.transpose, args=(stack_weights, 1, 2)
            )
            transpose_weight.meta["example_value"] = torch.transpose(
                stack_weights.meta["example_value"], 1, 2
            )
            if all(bias is None for bias in batch_biases):
                bmm = graph.call_function(  # type: ignore[operator]
                    torch.bmm,
                    args=(stack_inputs, transpose_weight),
                )
                bmm.meta["example_value"] = torch.bmm(
                    stack_inputs.meta["example_value"],
                    transpose_weight.meta["example_value"],
                )
                bmm_meta = bmm.meta["example_value"]
            else:
                stack_biases = graph.call_function(  # type: ignore[operator]
                    torch.stack, args=(batch_biases,), kwargs={"dim": 0}
                )
                update_stack_example_value(stack_biases, batch_biases_metadata)
                unsqueeze_biases = graph.call_function(  # type: ignore[operator]
                    torch.unsqueeze, args=(stack_biases, 1)
                )
                unsqueeze_biases.meta["example_value"] = torch.unsqueeze(
                    stack_biases.meta["example_value"], 1
                )
                bmm = graph.call_function(  # type: ignore[operator]
                    torch.baddbmm,
                    args=(unsqueeze_biases, stack_inputs, transpose_weight),
                )
                try:
                    # it will have runtime error to broadcast when it has dynamic shape included
                    # in the meta data, so we need to skip the update meta data
                    bmm.meta["example_value"] = torch.baddbmm(
                        unsqueeze_biases.meta["example_value"],
                        stack_inputs.meta["example_value"],
                        transpose_weight.meta["example_value"],
                    )
                    bmm_meta = bmm.meta["example_value"]
                except Exception as e:
                    log.debug(
                        f" exception when update bmm meta data with stack error tracekey {e}"  # noqa: G004
                    )
                    bmm_meta = None

            bmm = graph.call_function(torch.unbind, args=(bmm,), kwargs={"dim": 0})  # type: ignore[operator]
            if bmm_meta is not None:
                bmm.meta["example_value"] = torch.unbind(bmm_meta, dim=0)
            for i, linear in enumerate(batch_nodes):
                with graph.inserting_after(bmm):  # type: ignore[operator]
                    getitem = graph.call_function(operator.getitem, args=(bmm, i))  # type: ignore[operator]
                linear.replace_all_uses_with(getitem)
                getitem.meta.update(linear.meta)
                graph.erase_node(linear)  # type: ignore[operator]
        counters["inductor"]["batch_linear"] += 1