def _get_collective_node_from_wait(node: torch.fx.Node) -> torch.fx.Node | None:
    """Given a wait node, return the collective it waits on.

    Handles both standard (wait -> collective) and coalesced
    (wait -> getitem -> coalesced_collective) patterns.
    Returns None if the node is not a wait on a recognized NCCL collective.
    """
    if not is_wait_tensor(node):
        return None
    arg = node.args[0]
    assert isinstance(arg, torch.fx.Node)
    if arg.op != "call_function":
        return None
    if arg.target is operator.getitem:
        assert isinstance(arg.args[0], torch.fx.Node)
        arg = arg.args[0]
        if arg.op != "call_function":
            return None
    if not isinstance(arg.target, Callable):
        return None
    # pyrefly: ignore [missing-attribute]
    coll: NCCL_COLL = get_collective_type_from_kernel_name(arg.target.name())
    if coll == NCCL_COLL.UNSUPPORTED:
        return None
    return arg