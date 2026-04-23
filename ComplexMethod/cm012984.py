def _match(
    modules: dict[str, nn.ModuleDict],
    node: Node,
    current: nn.Module | Any,
) -> bool:
    r"""
    checks to see if a single node of a pattern matches
    """
    if isinstance(current, type) and issubclass(current, MatchAllNode):
        return True
    if not isinstance(node, Node):
        return False
    if isinstance(current, type) and issubclass(current, torch.nn.Module):
        return (
            node.op == "call_module"
            and parametrize.type_before_parametrizations(modules[node.target])  # type: ignore[index]
            == current
        )
    elif callable(current):
        return node.op == "call_function" and node.target is current
    elif isinstance(current, str):
        return node.target == current
    return False