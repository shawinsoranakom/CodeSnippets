def _try_remove_connecting_pytrees(curr_module_node: torch.fx.Node) -> None:
    """
    We want to try to remove extraneous pytree flatten/unflatten calls between modules
    calls. Instead of having the following:
    graph():
        ...
        %foo : [num_users=1] = call_module[target=foo](args = (%getitem_1, %getitem_2), kwargs = {})
        %tree_flatten_spec : [num_users=1] = call_function[target=torch.fx._pytree.tree_flatten_spec](args = (%foo, %_spec_1), kwargs = {})
        %getitem_4 : [num_users=1] = call_function[target=operator.getitem](args = (%tree_flatten_spec, 0), kwargs = {})
        %tree_unflatten_1 : [num_users=2] = call_function[target=torch.utils._pytree.tree_unflatten](args = ([%getitem_4], %_spec_2), kwargs = {})
        %getitem_5 : [num_users=1] = call_function[target=operator.getitem](args = (%tree_unflatten_1, 0), kwargs = {})
        %getitem_7 : [num_users=0] = call_function[target=operator.getitem](args = (%tree_unflatten_1, 1), kwargs = {})
        %getitem_6 : [num_users=1] = call_function[target=operator.getitem](args = (%getitem_5, 0), kwargs = {})
        %bar : [num_users=1] = call_module[target=bar](args = (%getitem_6,), kwargs = {})
        ...

    We could do the following, if we know that all the outputs of `foo` feed into `bar`:
    graph():
        ...
        %foo : [num_users=1] = call_module[target=foo](args = (%getitem_1, %getitem_2), kwargs = {})
        %bar : [num_users=1] = call_module[target=bar](args = (%getitem_6,), kwargs = {})
        ...

    Currently this optimization only works for the case where all of the outputs
    of `foo` go directly into `bar`, and `bar` has no other inputs.
    """

    log.debug("Trying to remove pytrees for module call %s", curr_module_node)

    curr_module_users = list(curr_module_node.users.keys())
    if len(curr_module_users) != 1:
        raise AssertionError(
            f"Expected only one user for module node, instead got {list(curr_module_users)}"
        )
    flatten_node = curr_module_users[0]
    if not (
        flatten_node.op == "call_function"
        and flatten_node.target is fx_pytree.tree_flatten_spec
    ):
        raise AssertionError(
            f"Expected flatten_node to be a call_function with target tree_flatten_spec, "
            f"but got op={flatten_node.op}, target={flatten_node.target}"
        )

    flatten_getitem_users = _get_getitem_users(flatten_node)
    if len(flatten_getitem_users) != 1:
        log.debug(
            "More than one user found for flatten node, %s: %s. "
            "Unable to fuse it with another unflatten call.",
            flatten_node,
            flatten_getitem_users,
        )
        return

    unflatten_node = next(iter(flatten_getitem_users))
    if not (
        unflatten_node.op == "call_function"
        and unflatten_node.target is pytree.tree_unflatten
    ):
        log.debug(
            "Flatten node %s's user is not a pytree.tree_unflatten. "
            "Instead it is: %s. Passing...",
            flatten_node,
            unflatten_node,
        )
        return

    for i, arg in enumerate(unflatten_node.args[0]):  # type: ignore[union-attr,arg-type]
        if arg not in flatten_node.users:
            log.debug(
                "Module %s's outputs are not all directly used as inputs to "
                "the subsequent module. Unable to fuse the connecting "
                "flatten/unflatten. The inputs to the subsequent module are: %s. ",
                curr_module_node,
                unflatten_node.args[0],
            )
            return

        if not (
            # pyrefly: ignore [missing-attribute]
            arg.op == "call_function"
            # pyrefly: ignore [missing-attribute]
            and arg.target is operator.getitem
            # pyrefly: ignore [missing-attribute]
            and arg.args[1] == i
        ):
            log.debug(
                "Module %s's outputs are not all directly used in the same "
                "order as outputted. Unable to fuse the connecting "
                "flatten/unflatten. The inputs to the "
                "subsequent module are: %s. ",
                curr_module_node,
                unflatten_node.args[0],
            )
            return

    # Unflatten has two levels of getitem, because it gets the args and kwargs
    unflatten_getitem_getitem_users = set()
    unflatten_getitem_users = _get_getitem_users(unflatten_node)
    for unflatten_getitem_user in unflatten_getitem_users:
        unflatten_getitem_getitem_users.update(
            list(unflatten_getitem_user.users.keys())
        )

    if len(unflatten_getitem_getitem_users) != 1:
        log.debug(
            "More than one user found for unflatten node, %s: %s. "
            "Unable to fuse it with another flatten call.",
            unflatten_node,
            unflatten_getitem_getitem_users,
        )
        return

    next_module_node = next(iter(unflatten_getitem_getitem_users))
    if next_module_node.op != "call_module":
        log.debug(
            "Unflatten node %s's user is not a call_module. "
            "Instead it is: %s. Passing...",
            unflatten_node,
            next_module_node,
        )
        return

    # Directly put the outputs of the current module into the next module
    next_module_node.args = (curr_module_node,)