def node_inline_(call_mod_node: torch.fx.Node) -> torch.fx.GraphModule | None:
    """
    Inline the submodule of the given node into the parent module.
    Note: we only support the case where submodule takes tensors inputs.
    """
    if call_mod_node.op != "call_module":
        raise AssertionError(f"expected call_module op, got {call_mod_node.op}")
    gm = call_mod_node.graph.owning_module
    if gm is None:
        raise AssertionError("owning_module should not be None")

    if not isinstance(call_mod_node.target, str):
        raise AssertionError(
            f"expected target to be str, got {type(call_mod_node.target).__name__}"
        )
    sub_gm = getattr(gm, call_mod_node.target)

    phs = (node for node in sub_gm.graph.nodes if node.op == "placeholder")
    body = (
        node for node in sub_gm.graph.nodes if node.op not in ("placeholder", "output")
    )
    output = [node for node in sub_gm.graph.nodes if node.op == "output"]

    for ph, arg in zip(phs, call_mod_node.args):
        if not isinstance(arg, torch.fx.Node):
            raise AssertionError(f"expected fx.Node, got {type(arg)}")
        node_replace_(ph, arg)

    with gm.graph.inserting_before(call_mod_node):
        for node in body:
            new_node = gm.graph.node_copy(node)
            if node.op == "get_attr":
                new_target_name = new_node.target
                if hasattr(gm, new_target_name):
                    # Loop through and find the "submod_{i}" that have no name collision
                    i = 1
                    new_target_name = f"submod_{i}"
                    while hasattr(gm, new_target_name):
                        i += 1
                        new_target_name = f"submod_{i}"
                new_node.target = new_target_name
                setattr(gm, new_node.target, getattr(sub_gm, node.target))
            node_replace_(node, new_node)

        if len(output) > 0:
            if len(output) != 1 or len(output[0].args) != 1:
                raise AssertionError(
                    f"expected exactly 1 output with 1 arg, got {len(output)} outputs"
                )
            new_output = output[0].args[0]

            if isinstance(new_output, torch.fx.Node):
                # Clear the users of the output node and set
                # the users to be the users of original call_module node.
                new_output.users.clear()
                node_replace_(call_mod_node, new_output)
            elif isinstance(new_output, (list, tuple)):
                # Pop subgraph output node from users.
                for node in new_output:
                    node.users.pop(output[0])

                # Inline the get_item calls for the output node.
                get_item_users = nodes_filter(
                    list(call_mod_node.users.keys()),
                    lambda node: node.op == "call_function"
                    and node.target is operator.getitem,
                )
                # get_item_node.args[1] is the idx referring to new_output[idx]
                nodes_map(
                    get_item_users,
                    lambda get_item_node: node_replace_(
                        get_item_node,
                        new_output[get_item_node.args[1]],
                    ),
                )
                call_mod_node.graph.erase_node(call_mod_node)
            else:
                raise NotImplementedError(
                    f"Unsupported output type {type(new_output)}. Expect it to be a Node or a list/tuple of Nodes."
                )
        else:
            call_mod_node.graph.erase_node(call_mod_node)

    gm.delete_all_unused_submodules()
    gm.recompile()
    return gm