def _replace_with_hop_helper(
    node: torch.fx.Node,
    enter_block_node: torch.fx.Node,
    wrap_hoo: HigherOrderOperator,
) -> None:
    graph: torch.fx.Graph = node.graph
    if graph.owning_module is None:
        raise AssertionError("graph.owning_module must not be None")
    gm: torch.fx.GraphModule = graph.owning_module
    if not isinstance(node.target, str):
        raise AssertionError(f"expected str target, got {type(node.target)}")
    sub_gm = getattr(gm, node.target)

    def set_hoo_node_meta(call_func_node):
        call_func_node.meta["nn_module_stack"] = copy.copy(
            enter_block_node.meta.get("nn_module_stack", {})
        )
        call_func_node.meta["torch_fn"] = (
            f"{wrap_hoo.__name__}",
            # pyrefly: ignore [missing-attribute]
            f"{wrap_hoo.__class__.__name__}.{wrap_hoo.__name__}",
        )
        if isinstance(output_args, (tuple, list)):
            call_func_node.meta["val"] = tuple(arg.meta["val"] for arg in output_args)
        elif isinstance(output_args, torch.fx.Node):
            call_func_node.meta["val"] = (output_args.meta["val"],)

    with graph.inserting_before(node):
        get_attr_node = graph.get_attr(node.target)
        get_attr_node.meta["nn_module_stack"] = copy.copy(
            enter_block_node.meta.get("nn_module_stack", {})
        )
        output_node = next(iter(reversed(sub_gm.graph.nodes)), None)
        # Split_module pass intentionally doesn't add output node
        # if the graph doesn't return anything.
        # TODO (tmanlaibaatar) Figure out if this is right behaviour
        # for split_module
        if isinstance(output_node, torch.fx.Node) and output_node.op != "output":
            output_node = None
        if output_node is not None:
            if len(output_node.args) != 1:
                raise AssertionError(
                    f"expected 1 output arg, got {len(output_node.args)}"
                )
            output_args = output_node.args[0]
            enter_block_node_args = enter_block_node.args
            if isinstance(output_args, (tuple, list)):
                call_func_node = graph.call_function(
                    wrap_hoo,
                    (*enter_block_node_args, get_attr_node, *node.args),
                    {},
                )
                # Create the metadata
                set_hoo_node_meta(call_func_node)
                node_replace_(node, call_func_node)

                # Rename the name of getitem nodes to the actual name of its contents
                # for passing verifier and better readability, also propagate metadata
                for get_item_node in call_func_node.users:
                    idx: int = get_item_node.args[1]  # type: ignore[assignment]
                    output_node = output_args[idx]
                    get_item_node._rename(output_node.name)
                    get_item_node.meta = output_node.meta

            elif isinstance(output_args, torch.fx.Node):
                call_func_node = graph.create_node(
                    "call_function",
                    wrap_hoo,
                    (*enter_block_node_args, get_attr_node, *node.args),
                    {},
                    output_args.name,
                )
                # Modify the subgraph to output a singleton list.
                output_node.args = ((output_args,),)
                # Add in an extra `getitem(wrap_hoo, 0)` node to the toplevel graph.
                get_item_node = graph.create_node(
                    "call_function",
                    operator.getitem,
                    (call_func_node, 0),
                    {},
                )
                # Create the metadata
                get_item_node.meta = output_args.meta
                set_hoo_node_meta(call_func_node)
                node_replace_(node, get_item_node)
            else:
                raise NotImplementedError(
                    f"replace_with_hop_pass doesn't support output type {type(output_args)}"
                )
        else:
            # TODO (shangdiy): remove this line, since the export graph can be non-functional
            node.graph.erase_node(node)