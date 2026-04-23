def thread_graphsafe_rng_from_hops(
    module: fx.GraphModule, is_backward: bool
) -> fx.GraphModule:
    """
    Graph-safe RNG lets torch.compile use CUDA Graphs for graphs with RNG ops.
    For graphs without HOPs, the partitioner adds placeholder nodes
    fwd_rng_state_* and bw_rng_state_* to the forward and backward graphs. At
    runtime, the AOTDispatcher retrieves these RNG states and passes them to the
    compiled graphs.

    This works well for no-HOP graphs. With HOPs, the partitioner runs
    recursively: it first partitions the HOP (producing forward/backward HOP
    subgraphs) and then stitches them back into the outer joint graph. For HOPs
    that contain RNG ops, the outer joint graph now includes HOP subgraph
    modules with extra RNG placeholders. We must thread these placeholders
    through the outer module partitioned forward and backward graphs—this
    function does exactly that. It collects the RNG placeholder nodes from the
    HOPs and creates corresponding placeholders in the outer forward and
    backward graphs.

    There is a catch: for a short period, the joint graph is in a “bad” state.
    The HOP subgraphs expect additional inputs (because of the new
    placeholders), but the outer graph call sites don't yet provide them. We
    can't fix this in the joint graph because the joint graph's input signature
    is fixed (primals, tangents). As a compromise, we keep the joint graph in
    somewhat of a bad state for some time and, once the outer forward and
    backward graphs are partitioned, insert the corresponding RNG placeholders
    and wire up the calls.
    """

    rng_count = 0
    rng_string = "bwd_rng_state" if is_backward else "fwd_rng_state"
    last_input = next(reversed(module.graph.find_nodes(op="placeholder")))
    for hop_node in module.graph.find_nodes(
        op="call_function", target=torch.ops.higher_order.invoke_subgraph
    ):
        subgraph = getattr(module, hop_node.args[0].target)
        if isinstance(subgraph, fx.GraphModule):
            new_rng_inputs: list[fx.Node] = []
            for placeholder_node in subgraph.graph.find_nodes(op="placeholder"):
                if rng_string in placeholder_node.name:
                    # Found a rng state placeholder in the hop graph, lets add
                    # the corresponding node in the outer graph
                    with module.graph.inserting_after(last_input):
                        rng_state = module.graph.placeholder(
                            f"{rng_string}_{rng_count}"
                        )
                        rng_count += 1
                        rng_state.meta["val"] = placeholder_node.meta["val"]
                        last_input = rng_state
                        new_rng_inputs.append(rng_state)

            if new_rng_inputs:
                # Pass on the new args that include the new_rng_inputs
                with module.graph.inserting_after(hop_node):
                    new_hop_node_with_fixed_args = module.graph.create_node(
                        "call_function",
                        torch.ops.higher_order.invoke_subgraph,
                        (*hop_node.args, *new_rng_inputs),  # type: ignore[arg-type]
                        {},
                    )
                    hop_node.replace_all_uses_with(
                        new_hop_node_with_fixed_args, propagate_meta=True
                    )

                # Setup the eager_input_vals
                eager_vals = hop_node.meta.get("eager_input_vals")
                if eager_vals:
                    eager_args, eager_kwargs = eager_vals
                    new_eager_args = (
                        *eager_args,
                        *[inp.meta["val"] for inp in new_rng_inputs],
                    )
                    new_hop_node_with_fixed_args.meta["eager_input_vals"] = (
                        new_eager_args,
                        eager_kwargs,
                    )
                module.graph.erase_node(hop_node)

    return module