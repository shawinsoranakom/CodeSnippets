def maybe_get_next_module(
    node: Node,
    modules: dict[str, nn.Module],
    target_module_type: type[nn.Module] | None = None,
    target_functional_type: Any = None,
) -> Node | None:
    """Gets the next module that matches what is needed in
    is_target_module_type if it exists

    Args:
        node: The node whose users we want to look at
        target_module_type: Module type that we want to check
        target_functional_type: Functional type that we want to check
    """

    for user in node.users:
        if (
            user.op == "call_module"
            and target_module_type is not None
            and isinstance(modules[str(user.target)], target_module_type)
        ):
            return user
        elif (
            user.op == "call_function"
            and target_functional_type is not None
            and user.target == target_functional_type
        ):
            return user

    return None