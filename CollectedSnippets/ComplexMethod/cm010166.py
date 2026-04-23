def _unused_constant(node: torch.fx.Node) -> list[torch.fx.Node] | None:
    """
    If there is a tensor constant created while tracing, here is how the graph
    looks like:

        %_tensor_constant0 : [num_users=1] = get_attr[target=_tensor_constant0]
        %lift_fresh_copy : [num_users=1] = call_function[target=torch.ops.aten.lift_fresh_copy.default](args = (%_tensor_constant0,))
        %detach_ : [num_users=?] = call_function[target=torch.ops.aten.detach_.default](args = (%lift_fresh_copy,))

    To check to see if the tensor constant is being used, we want to traverse to
    the detach node to see if it's actually being used.

    This function returns None if this constant is being used, otherwise it returns the
    lift_fresh and detach node to be removed later.
    """
    if len(node.users) > 1:
        return None

    lift_fresh_node = next(iter(node.users.keys()))
    if not (
        lift_fresh_node.op == "call_function"
        and lift_fresh_node.target
        in (
            torch.ops.aten.lift_fresh.default,
            torch.ops.aten.lift_fresh_copy.default,
        )
    ):
        return None

    if len(lift_fresh_node.users) > 1:
        return None

    # Case 1: lift node is not used anywhere
    if len(lift_fresh_node.users) == 0:
        return [lift_fresh_node, node]

    detach_node = next(iter(lift_fresh_node.users.keys()))
    if not (
        detach_node.op == "call_function"
        and detach_node.target
        in (
            torch.ops.aten.detach_.default,
            torch.ops.aten.detach.default,
        )
    ):
        return None

    if len(detach_node.users) > 0:
        return None
    else:
        # Case 2: Lift node's child is not used anywhere
        return [detach_node, lift_fresh_node, node]