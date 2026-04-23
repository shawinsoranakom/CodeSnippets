def apply_match(
    modules: dict[str, nn.ModuleDict],
    pattern: tuple[Any] | Any,
    node: Node,
    matched_node_pattern: list[Node],
) -> list[Node] | None:
    r"""
    This function will return the matched nodes if the pattern matches the node given
    If there is no match, it will return None
    """
    if isinstance(pattern, tuple):
        if len(pattern) == 1:
            if _match(modules, node, pattern[0]):
                return matched_node_pattern + [node]

        first, *rest = pattern
        if _match(modules, node, first):
            if rest is None:
                return matched_node_pattern + [node]

            for user in node.users:
                return apply_match(
                    modules, tuple(rest), user, matched_node_pattern + [node]
                )
    elif _match(modules, node, pattern):
        return [node]
    return None