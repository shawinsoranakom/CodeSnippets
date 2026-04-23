def _partitioner(gm: torch.fx.GraphModule) -> torch.fx.GraphModule:
    """
    Graph partitioner that partitions the single device graph
    to distributed graph
    """
    for node in gm.graph.nodes:
        node_sharding = node.meta["sharding"]
        if node.op == "placeholder":
            out_spec = node_sharding.output_spec
            local_val = _partition_val(node.meta["val"], out_spec)
            # update node value
            node.meta["val"] = local_val
        elif node.op == "call_function":
            out_spec = node_sharding.output_spec
            # check if there's misaligned sharding, insert reshard if there is
            expected_input_specs = node_sharding.input_specs
            for idx, input_arg in enumerate(node.all_input_nodes):
                input_arg_sharding = input_arg.meta["sharding"]
                input_arg_spec = input_arg_sharding.output_spec
                desired_spec = (
                    out_spec
                    if expected_input_specs is None
                    else expected_input_specs[idx]
                )
                if input_arg_spec != desired_spec:
                    _insert_reshard_gm(
                        gm, node, input_arg, input_arg_spec, desired_spec
                    )
            # convert output val to its local component
            output_val = node.meta["val"]
            node.meta["val"] = _partition_val(output_val, out_spec)
        elif node.op == "output":
            for input_arg in node.all_input_nodes:
                # input args of output should be Replicate, otherwise redistribution is needed.
                input_args_to_check: Sequence[Node] = (
                    input_arg if isinstance(input_arg, Sequence) else [input_arg]
                )
                for arg in input_args_to_check:
                    arg_sharding = arg.meta["sharding"]
                    arg_spec = arg_sharding.output_spec
                    desired_spec = copy.copy(arg_spec)
                    desired_spec.placements = (Replicate(),)
                    if arg_spec != desired_spec:
                        _insert_reshard_gm(gm, node, arg, arg_spec, desired_spec)
        else:
            raise RuntimeError(f"op code {node} not supported")

    _clean_up_graph_metadata(gm)
    gm.graph.lint()
    gm.recompile()
    return gm