def _replace_with_effects_node(
    node, ep, inputs_to_lifted_custom_objs, output_tokens, input_tokens, module
):
    """Replace a with_effects node with the underlying function call."""
    # Get the input nodes
    token_node, func, *node_args = node.args
    if token_node.op == "placeholder":
        input_tokens.append(token_node)

    if not isinstance(func, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)):
        raise AssertionError(
            f"Expected func to be an OpOverload or HigherOrderOperator, but got {type(func)}"
        )

    # Get the schema for the function
    if func is torch.ops.higher_order.call_torchbind:
        custom_obj = _get_custom_obj_for_node(
            node_args[0], inputs_to_lifted_custom_objs, ep.constants
        )
        schema = _get_schema(func, [custom_obj] + node_args[1:])
    else:
        schema = _get_schema(func, node_args)

    # Create the replacement node
    with module.graph.inserting_before(node):
        new_node = module.graph.call_function(func, tuple(node_args), node.kwargs)

    # Update getitem nodes that extract outputs from with_effects
    for user in list(node.users.keys()):
        if user.target is not operator.getitem:
            raise AssertionError(
                f"Expected user target to be operator.getitem, but got {user.target}"
            )
        # getitem(with_effects, 0) is the token node
        if user.args[1] == 0:
            for user_user in list(user.users.keys()):
                if user_user.op == "output":
                    output_tokens.append(user)

    # Copy metadata from old node to new node
    for k, v in node.meta.items():
        new_node.meta[k] = v
        if k == "unbacked_bindings":
            # Remove the extra layer for effect token
            old_bindings = new_node.meta[k]
            new_bindings = {
                k: path[1:] if path else path for k, path in old_bindings.items()
            }
            new_node.meta[k] = new_bindings

    # Fix up the getitem nodes based on return count
    if len(schema.returns) == 1:
        # Single return: replace getitem(with_effects, 1) with the node itself
        for user in list(node.users.keys()):
            if user.args[1] == 1:
                user.replace_all_uses_with(new_node)
        new_node.meta["val"] = node.meta["val"][1]
    elif len(schema.returns) > 1:
        # Multiple returns: shift getitem indices down by 1
        for user in list(node.users.keys()):
            if user.args[1] >= 1:
                user.args = (new_node, user.args[1] - 1)
        new_node.meta["val"] = node.meta["val"][1:]
    else:
        # No returns
        if len(schema.returns) != 0:
            raise AssertionError(
                f"Expected schema.returns to be empty, but got {len(schema.returns)} returns"
            )
        if len(new_node.users) != 0:
            raise AssertionError(
                f"Expected new_node to have no users, but got {len(new_node.users)} users"
            )
        new_node.meta["val"] = None