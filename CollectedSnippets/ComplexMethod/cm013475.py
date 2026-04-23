def matches_module_pattern(
    pattern: Iterable[type], node: fx.Node, modules: dict[str, torch.nn.Module]
) -> bool:
    if len(node.args) == 0:
        return False
    nodes: tuple[Argument, fx.Node] = (node.args[0], node)
    for expected_type, current_node in zip(pattern, nodes):
        if not isinstance(current_node, fx.Node):
            return False
        if current_node.op != "call_module":
            return False
        if not isinstance(current_node.target, str):
            return False
        if current_node.target not in modules:
            return False
        if type(modules[current_node.target]) is not expected_type:
            return False
    return True